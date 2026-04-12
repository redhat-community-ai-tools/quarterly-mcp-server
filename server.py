#!/usr/bin/env python3
"""
Quarterly MCP Server - Achievement tracking for quarterly reviews

Aggregates accomplishments from Jira, GitHub, and GitLab to generate
quarterly connection reports for performance reviews.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

from fastmcp import FastMCP
from jira import JIRA
import requests

# Initialize FastMCP server
mcp = FastMCP("quarterly-mcp-server")

# Load configuration
CONFIG_PATH = Path.home() / ".quarterly-mcp-config.json"

def load_config() -> Dict[str, Any]:
    """Load configuration from file or environment variables."""
    config = {}

    # Try loading from config file
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)

    # Override with environment variables if present
    config['jira_url'] = os.getenv('JIRA_URL', config.get('JIRA_URL', ''))
    config['jira_email'] = os.getenv('JIRA_EMAIL', config.get('JIRA_EMAIL', ''))
    config['jira_token'] = os.getenv('JIRA_API_TOKEN', config.get('JIRA_API_TOKEN', ''))
    config['github_token'] = os.getenv('GITHUB_TOKEN', config.get('GITHUB_TOKEN', ''))
    config['gitlab_url'] = os.getenv('GITLAB_URL', config.get('GITLAB_URL', 'https://gitlab.com'))
    config['gitlab_token'] = os.getenv('GITLAB_TOKEN', config.get('GITLAB_TOKEN', ''))

    return config

CONFIG = load_config()

# Initialize clients
def get_jira_client():
    """Initialize Jira client."""
    if not CONFIG['jira_url'] or not CONFIG['jira_token']:
        raise ValueError("Jira configuration missing. Set JIRA_URL and JIRA_API_TOKEN.")

    return JIRA(
        server=CONFIG['jira_url'],
        basic_auth=(CONFIG['jira_email'], CONFIG['jira_token'])
    )

def get_github_headers():
    """Get GitHub API headers."""
    if not CONFIG['github_token']:
        raise ValueError("GitHub token missing. Set GITHUB_TOKEN.")

    return {
        'Authorization': f'token {CONFIG["github_token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }

def get_gitlab_headers():
    """Get GitLab API headers."""
    if not CONFIG['gitlab_token']:
        return None

    return {
        'PRIVATE-TOKEN': CONFIG['gitlab_token']
    }


@mcp.tool()
def get_jira_summary(
    username: str,
    start_date: str,
    end_date: str,
    project: Optional[str] = None
) -> str:
    """
    Get Jira ticket summary for a date range.

    Args:
        username: Jira username or email
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        project: Optional project key filter (e.g., 'WINC')

    Returns:
        JSON summary of Jira activity
    """
    try:
        jira = get_jira_client()

        # Build JQL query
        jql = f'reporter = "{username}" AND created >= "{start_date}" AND created <= "{end_date}"'
        if project:
            jql = f'project = {project} AND {jql}'
        jql += ' ORDER BY created DESC'

        # Fetch issues
        issues = jira.search_issues(jql, maxResults=500)

        # Aggregate statistics
        stats = {
            'total': len(issues),
            'by_status': {},
            'by_type': {},
            'by_priority': {},
            'closed': 0,
            'in_progress': 0,
            'issues': []
        }

        for issue in issues:
            status = str(issue.fields.status)
            issue_type = str(issue.fields.issuetype)
            priority = str(issue.fields.priority) if issue.fields.priority else 'Undefined'

            # Count by status
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

            # Count by type
            stats['by_type'][issue_type] = stats['by_type'].get(issue_type, 0) + 1

            # Count by priority
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1

            # Track closed/in-progress
            if status == 'Closed':
                stats['closed'] += 1
            elif status in ['In Progress', 'In Review']:
                stats['in_progress'] += 1

            # Add issue details
            stats['issues'].append({
                'key': issue.key,
                'summary': issue.fields.summary,
                'status': status,
                'type': issue_type,
                'priority': priority,
                'created': issue.fields.created[:10],
                'resolved': issue.fields.resolutiondate[:10] if issue.fields.resolutiondate else None
            })

        # Calculate closure rate
        if stats['total'] > 0:
            stats['closure_rate'] = round((stats['closed'] / stats['total']) * 100, 1)
        else:
            stats['closure_rate'] = 0.0

        return json.dumps(stats, indent=2)

    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def get_github_summary(
    username: str,
    start_date: str,
    end_date: str,
    org: Optional[str] = None
) -> str:
    """
    Get GitHub PR summary for a date range.

    Args:
        username: GitHub username
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        org: Optional organization filter (e.g., 'openshift')

    Returns:
        JSON summary of GitHub activity
    """
    try:
        headers = get_github_headers()

        # Build GitHub search query
        query = f'author:{username} is:pr is:merged merged:{start_date}..{end_date}'
        if org:
            query = f'{query} org:{org}'

        # Search PRs
        url = f'https://api.github.com/search/issues?q={query}&per_page=100'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Aggregate statistics
        stats = {
            'total': data['total_count'],
            'by_repo': {},
            'prs': []
        }

        for pr in data['items']:
            repo = pr['repository_url'].split('/')[-1]
            owner = pr['repository_url'].split('/')[-2]
            repo_full = f'{owner}/{repo}'

            # Count by repository
            stats['by_repo'][repo_full] = stats['by_repo'].get(repo_full, 0) + 1

            # Add PR details
            stats['prs'].append({
                'number': pr['number'],
                'title': pr['title'],
                'repository': repo_full,
                'merged_at': pr['closed_at'][:10] if pr['closed_at'] else None,
                'url': pr['html_url']
            })

        return json.dumps(stats, indent=2)

    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def get_gitlab_summary(
    username: str,
    start_date: str,
    end_date: str,
    group: Optional[str] = None
) -> str:
    """
    Get GitLab MR summary for a date range.

    Args:
        username: GitLab username
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        group: Optional group filter (e.g., 'winc')

    Returns:
        JSON summary of GitLab activity
    """
    try:
        headers = get_gitlab_headers()
        if not headers:
            return json.dumps({'error': 'GitLab token not configured'})

        # Search merged MRs by author
        gitlab_url = CONFIG['gitlab_url']

        # Get user ID first
        user_response = requests.get(
            f'{gitlab_url}/api/v4/users?username={username}',
            headers=headers
        )
        user_response.raise_for_status()
        users = user_response.json()

        if not users:
            return json.dumps({'error': f'User {username} not found'})

        user_id = users[0]['id']

        # Get merged MRs
        params = {
            'author_id': user_id,
            'state': 'merged',
            'updated_after': start_date,
            'updated_before': end_date,
            'per_page': 100
        }

        if group:
            # Search within group
            url = f'{gitlab_url}/api/v4/groups/{group}/merge_requests'
        else:
            # Search all projects
            url = f'{gitlab_url}/api/v4/merge_requests'

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        mrs = response.json()

        # Aggregate statistics
        stats = {
            'total': len(mrs),
            'by_project': {},
            'mrs': []
        }

        for mr in mrs:
            project = mr['references']['full']

            # Count by project
            stats['by_project'][project] = stats['by_project'].get(project, 0) + 1

            # Add MR details
            stats['mrs'].append({
                'iid': mr['iid'],
                'title': mr['title'],
                'project': project,
                'merged_at': mr['merged_at'][:10] if mr['merged_at'] else None,
                'url': mr['web_url']
            })

        return json.dumps(stats, indent=2)

    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def generate_quarterly_report(
    username: str,
    quarter: int,
    year: int,
    jira_project: Optional[str] = None,
    github_org: Optional[str] = None,
    gitlab_group: Optional[str] = None,
    jira_username: Optional[str] = None,
    github_username: Optional[str] = None,
    gitlab_username: Optional[str] = None
) -> str:
    """
    Generate comprehensive quarterly achievement report.

    Args:
        username: Base username (used if platform-specific usernames not provided)
        quarter: Quarter number (1-4)
        year: Year (e.g., 2026)
        jira_project: Optional Jira project filter
        github_org: Optional GitHub organization filter
        gitlab_group: Optional GitLab group filter
        jira_username: Optional Jira-specific username (often email like user@domain.com)
        github_username: Optional GitHub-specific username
        gitlab_username: Optional GitLab-specific username

    Returns:
        Markdown formatted quarterly report
    """
    try:
        # Calculate date range
        quarter_starts = {
            1: (1, 1),
            2: (4, 1),
            3: (7, 1),
            4: (10, 1)
        }

        quarter_ends = {
            1: (3, 31),
            2: (6, 30),
            3: (9, 30),
            4: (12, 31)
        }

        start_month, start_day = quarter_starts[quarter]
        end_month, end_day = quarter_ends[quarter]

        start_date = f'{year}-{start_month:02d}-{start_day:02d}'
        end_date = f'{year}-{end_month:02d}-{end_day:02d}'

        # Use platform-specific usernames if provided, otherwise use base username
        jira_user = jira_username if jira_username else username
        github_user = github_username if github_username else username
        gitlab_user = gitlab_username if gitlab_username else username

        # Gather data from all sources
        jira_data = json.loads(get_jira_summary(jira_user, start_date, end_date, jira_project))
        github_data = json.loads(get_github_summary(github_user, start_date, end_date, github_org))
        gitlab_data = json.loads(get_gitlab_summary(gitlab_user, start_date, end_date, gitlab_group))

        # Generate markdown report
        report = f"""# Q{quarter} {year} Quarterly Accomplishments
**Period:** {start_date} to {end_date}

---

## Executive Summary

### Jira Activity
- **Total Issues Filed:** {jira_data.get('total', 0)}
- **Issues Closed:** {jira_data.get('closed', 0)}
- **Closure Rate:** {jira_data.get('closure_rate', 0)}%
- **In Progress:** {jira_data.get('in_progress', 0)}

#### Breakdown by Status
"""
        for status, count in sorted(jira_data.get('by_status', {}).items(), key=lambda x: -x[1]):
            report += f"- {status}: {count}\n"

        report += f"""
#### Breakdown by Type
"""
        for issue_type, count in sorted(jira_data.get('by_type', {}).items(), key=lambda x: -x[1]):
            report += f"- {issue_type}: {count}\n"

        report += f"""
### GitHub Activity
- **Total PRs Merged:** {github_data.get('total', 0)}

#### Breakdown by Repository
"""
        for repo, count in sorted(github_data.get('by_repo', {}).items(), key=lambda x: -x[1]):
            report += f"- {repo}: {count}\n"

        if gitlab_data.get('total', 0) > 0:
            report += f"""
### GitLab Activity
- **Total MRs Merged:** {gitlab_data.get('total', 0)}

#### Breakdown by Project
"""
            for project, count in sorted(gitlab_data.get('by_project', {}).items(), key=lambda x: -x[1]):
                report += f"- {project}: {count}\n"

        report += f"""
---

## Detailed Accomplishments

### Closed Jira Issues ({jira_data.get('closed', 0)})
"""
        closed_issues = [i for i in jira_data.get('issues', []) if i['status'] == 'Closed']
        for issue in closed_issues[:20]:  # Limit to first 20
            report += f"- **{issue['key']}**: {issue['summary']} ({issue['type']}, {issue['priority']})\n"

        if len(closed_issues) > 20:
            report += f"\n... and {len(closed_issues) - 20} more closed issues\n"

        report += f"""
### Merged GitHub PRs ({github_data.get('total', 0)})
"""
        for pr in github_data.get('prs', [])[:20]:  # Limit to first 20
            report += f"- **{pr['repository']}#{pr['number']}**: {pr['title']}\n"

        if len(github_data.get('prs', [])) > 20:
            report += f"\n... and {len(github_data.get('prs', [])) - 20} more PRs\n"

        if gitlab_data.get('total', 0) > 0:
            report += f"""
### Merged GitLab MRs ({gitlab_data.get('total', 0)})
"""
            for mr in gitlab_data.get('mrs', [])[:20]:
                report += f"- **{mr['project']}!{mr['iid']}**: {mr['title']}\n"

            if len(gitlab_data.get('mrs', [])) > 20:
                report += f"\n... and {len(gitlab_data.get('mrs', [])) - 20} more MRs\n"

        report += f"""
---

**Generated:** {datetime.now().strftime('%Y-%m-%d')}
**Tool:** quarterly-mcp-server
"""

        return report

    except Exception as e:
        return f"Error generating report: {str(e)}"


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
