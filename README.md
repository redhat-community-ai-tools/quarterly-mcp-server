# Quarterly Report Tools

**AI-powered performance review automation for quarterly achievement reports.**

Automate your quarterly reviews by aggregating Jira, GitHub, and GitLab data, analyzing cycle times, identifying top achievements, and transforming technical descriptions into polished narratives.

## Two Ways to Use

### 1. Claude Code Skill (Recommended for Quarterly Reports)

**Best for:** Quarterly performance reviews (run once per quarter)

**Advantages:**
- Loaded on-demand (token efficient)
- Uses CLI tools directly (jira, gh, glab)
- No MCP server required
- Perfect for `/quarterly-report` workflow

**Installation:** See [.claude-code/README.md](.claude-code/README.md)

### 2. MCP Server (For Always-Available Tools)

**Best for:** Frequent queries throughout the quarter

**Advantages:**
- Always-available tools in any Claude Code session
- Programmatic API via Python functions
- Can be called by other tools/agents

**Installation:** See [MCP Server Setup](#mcp-server-setup) below

---

**TL;DR:** Use the **Skill** for quarterly reports. Use the **MCP Server** only if you need daily Jira/GitHub queries.

---

# MCP Server Setup

## Features

- **Multi-platform aggregation**: Combines data from Jira, GitHub, and GitLab
- **Flexible date ranges**: Query any time period, with built-in quarterly report generation
- **Rich statistics**: Ticket counts, PR counts, closure rates, breakdowns by status/type/priority
- **Cycle time analysis**: Identify longest-running PRs and issues with average cycle times
- **AI-powered achievement identification**: Rank accomplishments by cycle time, impact, or complexity
- **Achievement refinement**: Transform technical descriptions into polished performance review narratives
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

### `analyze_cycle_times`

Analyze cycle times for Jira issues and GitHub PRs to identify longest-running work.

**Parameters:**
- `username` (required): Base username (used if platform-specific usernames not provided)
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `jira_project` (optional): Jira project filter
- `github_org` (optional): GitHub organization filter
- `jira_username` (optional): Jira-specific username (email)
- `github_username` (optional): GitHub-specific username
- `top_n` (optional): Number of top items to return (default: 10)

**Returns:** JSON with average cycle times and longest-running items from both platforms.

**Example:**
```
Analyze my cycle times for Q1 2026 (username: rrasouli, jira_username: rrasouli@redhat.com, start_date: 2026-01-01, end_date: 2026-03-31, jira_project: WINC, github_org: openshift)
```

### `identify_top_achievements`

Identify top achievements ranked by cycle time, impact, or complexity.

**Parameters:**
- `username` (required): Base username
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `metric` (optional): Ranking metric - "cycle_time" (longest work), "impact" (most complex), or "recent" (latest). Default: "cycle_time"
- `jira_project` (optional): Jira project filter
- `github_org` (optional): GitHub organization filter
- `jira_username` (optional): Jira-specific username
- `github_username` (optional): GitHub-specific username
- `top_n` (optional): Number of top achievements to return (default: 5)

**Returns:** JSON with ranked achievements and context for narrative building.

**Example:**
```
Identify my top 5 achievements by impact for Q1 2026 (username: rrasouli, metric: impact, start_date: 2026-01-01, end_date: 2026-03-31)
```

### `refine_achievement`

Transform technical PR/Jira description into polished achievement narrative for performance reviews.

**Parameters:**
- `raw_description` (required): Technical description (e.g., "Added AWS UPI jobs across 5 releases")
- `context` (optional): Additional context (PR metadata, Jira details, team impact)
- `style` (optional): Narrative style - "business_impact", "technical_depth", or "leadership". Default: "business_impact"

**Returns:** Refinement guide and examples for transforming technical descriptions into polished narratives.

**Example:**
```
Refine this achievement: "Added AWS UPI jobs across 5 releases" with business_impact style
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

### AI-Powered Performance Review Workflow

**Step 1: Analyze cycle times**
```
Analyze my Q1 2026 cycle times (username: jdoe, jira_username: jdoe@company.com, start_date: 2026-01-01, end_date: 2026-03-31, jira_project: MYPROJECT, github_org: myorg)
```

**Step 2: Identify top achievements**
```
Identify my top 5 achievements by impact for Q1 2026 (username: jdoe, metric: impact, start_date: 2026-01-01, end_date: 2026-03-31)
```

**Step 3: Refine each achievement**
```
Refine this achievement: "Added infrastructure support for BYOH provisioning" with business_impact style and context: "37 files changed, +666 lines, 17 days, enables all future BYOH testing"
```

**Step 4: Generate full report**
```
Generate my Q1 2026 quarterly report (username: jdoe, quarter: 1, year: 2026, jira_project: MYPROJECT, github_org: myorg)
```

This workflow transforms hours of manual review preparation into 30 minutes of focused refinement.

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
- Support for additional platforms (Linear, Asana, Prow CI, Jenkins)
- Export to different formats (CSV, JSON, PDF)
- Recognition mining (extract peer kudos from PR/issue comments)
- Team aggregation features
- Interactive review dialog (guided achievement narrative building)
- Data-driven goal setting (suggest goals based on historical velocity)
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
