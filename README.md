# Quarterly MCP Server

**Model Context Protocol (MCP) server for generating quarterly achievement reports from Jira, GitHub, and GitLab.**

Automate your quarterly connection reports by aggregating accomplishments across multiple platforms. Perfect for performance reviews, quarterly check-ins, and team retrospectives.

## Features

- **Multi-platform aggregation**: Combines data from Jira, GitHub, and GitLab
- **Flexible date ranges**: Query any time period, with built-in quarterly report generation
- **Rich statistics**: Ticket counts, PR counts, closure rates, breakdowns by status/type/priority
- **MCP integration**: Works with Claude Code, Claude Desktop, and other MCP clients
- **Team-friendly**: Anyone with MCP can use it for their own quarterly reviews

## Quick Start

### 1. Installation

```bash
git clone https://github.com/redhat-community-ai-tools/quarterly-mcp-server.git
cd quarterly-mcp-server
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration

Create `~/.quarterly-mcp-config.json`:

```json
{
  "JIRA_URL": "https://your-jira-instance.atlassian.net",
  "JIRA_EMAIL": "your-email@example.com",
  "JIRA_API_TOKEN": "your-jira-api-token",
  "GITHUB_TOKEN": "your-github-personal-access-token",
  "GITLAB_URL": "https://gitlab.com",
  "GITLAB_TOKEN": "your-gitlab-token"
}
```

**Getting API tokens:**
- **Jira**: https://id.atlassian.com/manage-profile/security/api-tokens
- **GitHub**: https://github.com/settings/tokens (need `repo` scope)
- **GitLab**: https://gitlab.com/-/profile/personal_access_tokens (need `read_api` scope)

**Note:** GitLab is optional. If you don't use GitLab, omit `GITLAB_TOKEN`.

### 3. Register with Claude Code

```bash
claude mcp add quarterly /path/to/quarterly-mcp-server/venv/bin/python -- /path/to/quarterly-mcp-server/server.py
```

Verify registration:

```bash
claude mcp list
```

### 4. Test It

Start a Claude Code session and ask:

```
Generate my Q1 2026 quarterly report (username: myusername, jira project: MYPROJECT, github org: myorg)
```

## MCP Tools

The server exposes these tools for use in Claude Code or other MCP clients:

### `get_jira_summary`

Get Jira ticket summary for a date range.

**Parameters:**
- `username` (required): Jira username or email
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `project` (optional): Project key filter (e.g., 'WINC')

**Example:**
```
Get my Jira summary for Q1 2026 (username: rrasouli@redhat.com, project: WINC, start: 2026-01-01, end: 2026-03-31)
```

### `get_github_summary`

Get GitHub PR summary for a date range.

**Parameters:**
- `username` (required): GitHub username
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `org` (optional): Organization filter (e.g., 'openshift')

**Example:**
```
Get my GitHub PRs for Q1 2026 (username: rrasouli, org: openshift, start: 2026-01-01, end: 2026-03-31)
```

### `get_gitlab_summary`

Get GitLab MR summary for a date range.

**Parameters:**
- `username` (required): GitLab username
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `group` (optional): Group filter (e.g., 'winc')

**Example:**
```
Get my GitLab MRs for Q1 2026 (username: rrasouli, group: winc, start: 2026-01-01, end: 2026-03-31)
```

### `generate_quarterly_report`

Generate comprehensive quarterly achievement report combining all platforms.

**Parameters:**
- `username` (required): Username (same across platforms)
- `quarter` (required): Quarter number (1-4)
- `year` (required): Year (e.g., 2026)
- `jira_project` (optional): Jira project filter
- `github_org` (optional): GitHub organization filter
- `gitlab_group` (optional): GitLab group filter

**Example:**
```
Generate my Q2 2026 quarterly report (username: rrasouli, quarter: 2, year: 2026, jira_project: WINC, github_org: openshift)
```

## Usage Examples

### Basic Quarterly Report

```
Generate my Q1 2026 quarterly report (username: jdoe, quarter: 1, year: 2026)
```

### Filtered by Project/Organization

```
Generate my Q2 2026 report for WINC project and openshift org (username: jdoe, quarter: 2, year: 2026, jira_project: WINC, github_org: openshift)
```

### Custom Date Range

```
Get my Jira summary from 2026-01-15 to 2026-02-15 (username: jdoe, start_date: 2026-01-15, end_date: 2026-02-15)
```

### Individual Platform Queries

```
Get my GitHub PRs merged in March 2026 (username: jdoe, start_date: 2026-03-01, end_date: 2026-03-31, org: redhat)
```

## Output Format

The `generate_quarterly_report` tool produces a markdown report with:

- **Executive Summary**: High-level statistics across all platforms
- **Jira Activity**: Total issues, closure rate, breakdowns by status/type/priority
- **GitHub Activity**: Total PRs merged, breakdown by repository
- **GitLab Activity**: Total MRs merged, breakdown by project (if configured)
- **Detailed Accomplishments**: Lists of closed issues and merged PRs/MRs

## For Managers

Managers can use this tool to:

1. **Generate team reports**: Query each team member's accomplishments
2. **Compare quarters**: Track team velocity over time
3. **Identify bottlenecks**: See closure rates and in-progress work
4. **Aggregate metrics**: Combine individual reports for team-level summaries

Example manager query:
```
Generate quarterly reports for my team (Alice: alice@example.com, Bob: bob@example.com, Carol: carol@example.com) for Q1 2026 in the TEAM project
```

## Configuration Options

You can configure the server via:

1. **Config file** (`~/.quarterly-mcp-config.json`)
2. **Environment variables** (override config file):
   - `JIRA_URL`
   - `JIRA_EMAIL`
   - `JIRA_API_TOKEN`
   - `GITHUB_TOKEN`
   - `GITLAB_URL`
   - `GITLAB_TOKEN`

Environment variables take precedence over config file values.

## Troubleshooting

### "Jira configuration missing" error

Make sure `JIRA_URL` and `JIRA_API_TOKEN` are set in your config file or environment.

### "GitHub token missing" error

Make sure `GITHUB_TOKEN` is set in your config file or environment.

### Authentication failures

- **Jira**: Verify your email and API token are correct
- **GitHub**: Ensure your token has `repo` scope
- **GitLab**: Ensure your token has `read_api` scope

### No results returned

- Check the date range (YYYY-MM-DD format)
- Verify the username matches your platform username
- For Jira: Check if the project key is correct
- For GitHub: Check if the org name is correct

## Contributing

Contributions welcome! This tool is designed for the Red Hat community but useful for anyone doing quarterly reviews.

**How to contribute:**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

**Ideas for contributions:**
- Support for additional platforms (Linear, Asana, etc.)
- Export to different formats (CSV, JSON, PDF)
- Velocity trend analysis
- Team aggregation features
- Slack/email integration for automated reports

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Related Projects

- [ci-failure-tracker](https://github.com/redhat-community-ai-tools/ci-failure-tracker) - Automated CI failure tracking and reporting
- [ci-dashboard](https://github.com/redhat-community-ai-tools/ci-dashboard) - CI test pass rate visualization

## Support

- **Issues**: https://github.com/redhat-community-ai-tools/quarterly-mcp-server/issues
- **Discussions**: https://github.com/redhat-community-ai-tools/quarterly-mcp-server/discussions

---

**Built with FastMCP** | **Part of the Red Hat Community AI Tools**
