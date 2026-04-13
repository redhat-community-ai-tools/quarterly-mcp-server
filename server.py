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
def analyze_cycle_times(
    username: str,
    start_date: str,
    end_date: str,
    jira_project: Optional[str] = None,
    github_org: Optional[str] = None,
    jira_username: Optional[str] = None,
    github_username: Optional[str] = None,
    top_n: int = 10
) -> str:
    """
    Analyze cycle times for Jira issues and GitHub PRs.

    Args:
        username: Base username (used if platform-specific usernames not provided)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        jira_project: Optional Jira project filter
        github_org: Optional GitHub organization filter
        jira_username: Optional Jira-specific username
        github_username: Optional GitHub-specific username
        top_n: Number of top items to return (default: 10)

    Returns:
        JSON with cycle time statistics and longest-running items
    """
    try:
        jira_user = jira_username if jira_username else username
        github_user = github_username if github_username else username

        # Get data from both sources
        jira_data = json.loads(get_jira_summary(jira_user, start_date, end_date, jira_project))
        github_data = json.loads(get_github_summary(github_user, start_date, end_date, github_org))

        # Calculate Jira cycle times
        jira_cycle_times = []
        for issue in jira_data.get('issues', []):
            if issue['resolved']:
                created = datetime.strptime(issue['created'], '%Y-%m-%d')
                resolved = datetime.strptime(issue['resolved'], '%Y-%m-%d')
                days = (resolved - created).days
                jira_cycle_times.append({
                    'key': issue['key'],
                    'summary': issue['summary'],
                    'type': issue['type'],
                    'status': issue['status'],
                    'cycle_days': days
                })

        # Sort by cycle time (longest first)
        jira_cycle_times.sort(key=lambda x: x['cycle_days'], reverse=True)

        # Calculate GitHub PR cycle times
        github_cycle_times = []
        for pr in github_data.get('prs', []):
            if pr['merged_at']:
                # Need to fetch PR details to get created_at
                try:
                    headers = get_github_headers()
                    pr_url = pr['url'].replace('https://github.com/', 'https://api.github.com/repos/')
                    pr_response = requests.get(pr_url, headers=headers)
                    pr_response.raise_for_status()
                    pr_details = pr_response.json()

                    created = datetime.strptime(pr_details['created_at'][:10], '%Y-%m-%d')
                    merged = datetime.strptime(pr['merged_at'], '%Y-%m-%d')
                    days = (merged - created).days

                    github_cycle_times.append({
                        'number': pr['number'],
                        'title': pr['title'],
                        'repository': pr['repository'],
                        'cycle_days': days,
                        'url': pr['url']
                    })
                except Exception as e:
                    # Skip PRs we can't fetch details for
                    continue

        # Sort by cycle time (longest first)
        github_cycle_times.sort(key=lambda x: x['cycle_days'], reverse=True)

        # Calculate averages
        jira_avg = sum(x['cycle_days'] for x in jira_cycle_times) / len(jira_cycle_times) if jira_cycle_times else 0
        github_avg = sum(x['cycle_days'] for x in github_cycle_times) / len(github_cycle_times) if github_cycle_times else 0

        result = {
            'jira': {
                'average_days': round(jira_avg, 1),
                'total_analyzed': len(jira_cycle_times),
                'longest': jira_cycle_times[:top_n]
            },
            'github': {
                'average_days': round(github_avg, 1),
                'total_analyzed': len(github_cycle_times),
                'longest': github_cycle_times[:top_n]
            }
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def identify_top_achievements(
    username: str,
    start_date: str,
    end_date: str,
    metric: str = "cycle_time",
    jira_project: Optional[str] = None,
    github_org: Optional[str] = None,
    jira_username: Optional[str] = None,
    github_username: Optional[str] = None,
    top_n: int = 5
) -> str:
    """
    Identify top achievements by cycle time, impact, or complexity.

    Args:
        username: Base username
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        metric: Ranking metric - "cycle_time" (longest work), "impact" (most complex), or "recent" (latest)
        jira_project: Optional Jira project filter
        github_org: Optional GitHub organization filter
        jira_username: Optional Jira-specific username
        github_username: Optional GitHub-specific username
        top_n: Number of top achievements to return (default: 5)

    Returns:
        JSON with ranked achievements and context for narrative building
    """
    try:
        # Get cycle time analysis
        cycle_data = json.loads(analyze_cycle_times(
            username, start_date, end_date,
            jira_project, github_org,
            jira_username, github_username,
            top_n=100  # Get more data for filtering
        ))

        achievements = []

        # Process GitHub PRs
        for pr in cycle_data.get('github', {}).get('longest', []):
            achievements.append({
                'type': 'github_pr',
                'identifier': f"{pr['repository']}#{pr['number']}",
                'title': pr['title'],
                'cycle_days': pr['cycle_days'],
                'repository': pr['repository'],
                'url': pr['url'],
                'score': pr['cycle_days']  # Default scoring by cycle time
            })

        # Process Jira issues
        for issue in cycle_data.get('jira', {}).get('longest', []):
            achievements.append({
                'type': 'jira_issue',
                'identifier': issue['key'],
                'title': issue['summary'],
                'cycle_days': issue['cycle_days'],
                'issue_type': issue['type'],
                'score': issue['cycle_days']  # Default scoring by cycle time
            })

        # Apply ranking based on metric
        if metric == "cycle_time":
            achievements.sort(key=lambda x: x['score'], reverse=True)
        elif metric == "recent":
            achievements.sort(key=lambda x: x['cycle_days'])  # Shorter cycle time = more recent
        elif metric == "impact":
            # Impact heuristic: longer cycle time + specific keywords
            for achievement in achievements:
                title_lower = achievement['title'].lower()
                impact_score = achievement['cycle_days']

                # Boost score for infrastructure keywords
                if any(word in title_lower for word in ['infrastructure', 'foundational', 'framework', 'template', 'automation']):
                    impact_score *= 1.5

                # Boost for multi-release work
                if any(word in title_lower for word in ['release', 'backport', 'multi-', 'across']):
                    impact_score *= 1.3

                achievement['score'] = impact_score

            achievements.sort(key=lambda x: x['score'], reverse=True)

        # Return top N
        result = {
            'metric': metric,
            'top_achievements': achievements[:top_n],
            'total_analyzed': len(achievements),
            'summary': {
                'github_prs': len([a for a in achievements if a['type'] == 'github_pr']),
                'jira_issues': len([a for a in achievements if a['type'] == 'jira_issue'])
            }
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def refine_achievement(
    raw_description: str,
    context: Optional[str] = None,
    style: str = "business_impact"
) -> str:
    """
    Transform technical PR/Jira description into polished achievement narrative.

    This tool provides a framework for refining achievement descriptions.
    The actual refinement should be done by Claude based on the style guide.

    Args:
        raw_description: Technical description (e.g., "Added AWS UPI jobs")
        context: Optional context (PR metadata, Jira details, team impact)
        style: Narrative style - "business_impact", "technical_depth", or "leadership"

    Returns:
        Guidance for refining the achievement narrative
    """
    style_guides = {
        "business_impact": """
Transform the technical description to emphasize:
- WHAT problem this solves for customers/users
- HOW this enables business objectives
- WHO benefits (team, customers, enterprise)
- WHY this matters strategically

Example transformation:
Before: "Added AWS UPI jobs across 5 releases"
After: "Enabled comprehensive Windows testing for enterprise customers using user-provisioned infrastructure, delivering single PR covering 5 active OpenShift releases instead of separate efforts - demonstrating efficient delivery and multi-release thinking"
""",
        "technical_depth": """
Transform the technical description to emphasize:
- WHAT technical challenges were solved
- HOW you approached the problem (architecture, design decisions)
- Technical complexity and scope (lines changed, files affected)
- Engineering rigor (testing, validation, production deployment)

Example transformation:
Before: "Consolidated test templates"
After: "Architected consolidation of 23 static YAML files into 3 parameterized Go templates (+1,280/-1,257 lines), building 11 resource code generators for programmatic generation. Created single source of truth eliminating copy-paste errors and enabling future OTE migration"
""",
        "leadership": """
Transform the technical description to emphasize:
- HOW you influenced outcomes beyond individual contribution
- WHAT decisions you made and why
- WHO you helped or unblocked
- Strategic thinking and judgment calls

Example transformation:
Before: "Fixed vSphere proxy job"
After: "Investigated AWS proxy limitation, discovered bootstrap blocker, made strategic pivot to vSphere platform. Documented decision-making process in PR description for team knowledge sharing. Filled coverage gap with proven pattern rather than forcing broken approach"
"""
    }

    guide = style_guides.get(style, style_guides["business_impact"])

    result = {
        "raw_description": raw_description,
        "context": context or "No additional context provided",
        "style": style,
        "refinement_guide": guide,
        "next_steps": "Use this guide to refine the raw description. Focus on transforming technical details into narratives that highlight impact, decision-making, and strategic value."
    }

    return json.dumps(result, indent=2)


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
