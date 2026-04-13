# Installation Guide

## Quick Start

This tool works in **three modes**:

1. **Claude Code Skill** (Recommended) - On-demand, token efficient
2. **Cursor** - IDE-agnostic workflow
3. **MCP Server** - Always-available tools for frequent queries

---

## Mode 1: Claude Code Skill (Recommended)

**Best for:** Quarterly performance reviews (run once per quarter)

### Installation

```bash
# 1. Install CLI tools
brew install jira-cli gh glab
jira init
gh auth login
glab auth login  # optional

# 2. Clone to plugins directory
mkdir -p ~/.claude/plugins
cd ~/.claude/plugins
git clone https://github.com/redhat-community-ai-tools/quarterly-mcp-server.git quarterly-report-assistant
```

### Usage

In any Claude Code session:

```
/quarterly-report
```

Claude will guide you through the four-phase workflow automatically.

---

## Mode 2: Cursor (IDE-Agnostic)

**Best for:** Using in Cursor, Windsurf, or any IDE with Claude integration

### Installation

```bash
# 1. Install CLI tools (same as above)
brew install jira-cli gh glab
jira init
gh auth login
glab auth login  # optional

# 2. Add to your project or global config
cd your-workspace
curl -O https://raw.githubusercontent.com/redhat-community-ai-tools/quarterly-mcp-server/master/QUARTERLY_REPORT_ASSISTANT.md

# Optional: Add .cursorrules for auto-detection
curl -O https://raw.githubusercontent.com/redhat-community-ai-tools/quarterly-mcp-server/master/.cursorrules
```

### Usage in Cursor

**Method 1: Reference the file**
```
@QUARTERLY_REPORT_ASSISTANT.md generate my Q1 2026 quarterly report
```

**Method 2: Use trigger phrases**
```
Generate my quarterly report for Q1 2026
```

Cursor will auto-detect via .cursorrules and load the workflow.

**Method 3: Explicit instruction**
```
Follow the quarterly report assistant workflow in QUARTERLY_REPORT_ASSISTANT.md to analyze my Q1 2026 achievements
```

### Usage in Other IDEs

In Windsurf, Zed, or any IDE with Claude integration:

```
Read QUARTERLY_REPORT_ASSISTANT.md and follow the four-phase workflow to generate my Q1 2026 quarterly report
```

---

## Mode 3: MCP Server (Advanced)

**Best for:** Frequent queries throughout the quarter, automation, other tools calling it

### Installation

```bash
# 1. Clone and setup
git clone https://github.com/redhat-community-ai-tools/quarterly-mcp-server.git
cd quarterly-mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure credentials
cat > ~/.quarterly-mcp-config.json <<EOF
{
  "JIRA_URL": "https://your-jira.atlassian.net",
  "JIRA_EMAIL": "you@example.com",
  "JIRA_API_TOKEN": "your-jira-api-token",
  "GITHUB_TOKEN": "your-github-token",
  "GITLAB_URL": "https://gitlab.com",
  "GITLAB_TOKEN": "your-gitlab-token-optional"
}
EOF

# 3. Register with Claude Code
claude mcp add quarterly $(pwd)/venv/bin/python -- $(pwd)/server.py
```

### Usage

MCP tools are always available:

```
# In any Claude Code session
analyze_cycle_times for Q1 2026
identify_top_achievements by impact
generate_quarterly_report for Q1 2026
```

---

## Comparison Table

| Feature | Claude Code Skill | Cursor | MCP Server |
|---------|------------------|---------|------------|
| **Token Usage** | Low (on-demand) | Low (on-demand) | High (always loaded) |
| **Setup Complexity** | Easy (clone to plugins) | Easy (add file to workspace) | Medium (venv + config) |
| **CLI Tools Required** | jira, gh, glab | jira, gh, glab | No (uses API directly) |
| **Configuration** | CLI auth | CLI auth | ~/.quarterly-mcp-config.json |
| **Invocation** | `/quarterly-report` | Mention in chat | Tools always available |
| **IDE Support** | Claude Code only | Any IDE | Claude Code only |
| **Best For** | Quarterly reports in Claude Code | Any IDE, quarterly reports | Frequent queries, automation |

---

## Recommended Setup by Use Case

**I want quarterly reports in Claude Code:**
→ Use **Claude Code Skill** (Mode 1)

**I use Cursor or other IDEs:**
→ Use **Cursor/IDE-Agnostic** (Mode 2)

**I query Jira/GitHub data frequently:**
→ Use **MCP Server** (Mode 3)

**I want maximum portability:**
→ Use **Cursor/IDE-Agnostic** (Mode 2) - works everywhere

---

## Verification

After installation, verify setup:

### Claude Code Skill
```bash
# Check plugin is installed
ls ~/.claude/plugins/quarterly-report-assistant/

# In Claude Code session, verify skill loads
/quarterly-report
```

### Cursor
```bash
# Check file exists in workspace
ls QUARTERLY_REPORT_ASSISTANT.md

# In Cursor, test reference
@QUARTERLY_REPORT_ASSISTANT.md
```

### MCP Server
```bash
# Check server is registered
claude mcp list | grep quarterly

# Check configuration
cat ~/.quarterly-mcp-config.json
```

---

## Getting API Tokens

### Jira API Token
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create new token
3. Copy token value
4. Use in `jira init` or MCP config

### GitHub Token
1. Go to https://github.com/settings/tokens
2. Create new token (classic)
3. Select scopes: `repo`, `read:org`
4. Copy token value
5. Use in `gh auth login` or MCP config

### GitLab Token
1. Go to https://gitlab.com/-/profile/personal_access_tokens
2. Create new token
3. Select scopes: `read_api`, `read_repository`
4. Copy token value
5. Use in `glab auth login` or MCP config

---

## Troubleshooting

### CLI Tools Not Found

```bash
# Check if installed
command -v jira || echo "Install: brew install jira-cli"
command -v gh || echo "Install: brew install gh"
command -v glab || echo "Install: brew install glab"
```

### Authentication Issues

```bash
# Re-authenticate Jira
jira init

# Re-authenticate GitHub
gh auth refresh

# Re-authenticate GitLab
glab auth login
```

### Claude Code Skill Not Loading

```bash
# Verify plugin directory structure
ls -la ~/.claude/plugins/quarterly-report-assistant/.claude-code/

# Check manifest exists
cat ~/.claude/plugins/quarterly-report-assistant/.claude-code/manifest.json

# Restart Claude Code
```

### Cursor Not Detecting

```bash
# Verify files in workspace
ls QUARTERLY_REPORT_ASSISTANT.md
ls .cursorrules

# Check file permissions
chmod +r QUARTERLY_REPORT_ASSISTANT.md
```

---

## Support

- **Issues**: https://github.com/redhat-community-ai-tools/quarterly-mcp-server/issues
- **Discussions**: https://github.com/redhat-community-ai-tools/quarterly-mcp-server/discussions
- **Documentation**: See README.md

---

**Part of Red Hat Community AI Tools** | **Apache License 2.0**
