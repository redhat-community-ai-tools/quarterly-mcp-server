# Quarterly Report Assistant

**AI-powered performance review automation through cycle time analysis and narrative refinement.**

> **Usage in Claude Code:** `/quarterly-report` or reference this file  
> **Usage in Cursor:** Add this file to workspace and reference with `@QUARTERLY_REPORT_ASSISTANT.md`  
> **Usage anywhere:** Ask Claude to "follow the quarterly report assistant workflow"

---

## What This Does

Transforms quarterly review preparation from **4-6 hours of manual work** into **30 minutes of focused refinement**:

1. Aggregates data from Jira, GitHub, GitLab using CLI tools
2. Analyzes cycle times to identify longest-running strategic work
3. Ranks achievements by cycle time, impact keywords, and complexity
4. Transforms technical descriptions into polished business-impact narratives
5. Generates enhanced markdown reports ready for performance reviews

## Prerequisites

### Required CLI Tools

**Must have:**
```bash
# Jira CLI
brew install jira-cli
jira init

# GitHub CLI
brew install gh
gh auth login
```

**Optional:**
```bash
# GitLab CLI (if you use GitLab)
brew install glab
glab auth login
```

### Verify Installation

```bash
jira me          # Shows your Jira user info
gh api user      # Shows your GitHub username
glab api user    # (Optional) Shows GitLab username
```

---

## Four-Phase Workflow

### Phase 1: Information Gathering

Ask the user for:

1. **Quarter and year** (e.g., Q1 2026)
2. **Jira username** (usually email: user@company.com)
3. **GitHub username** (handle, e.g., jdoe)
4. **GitLab username** (optional, if using GitLab)
5. **Jira project filter** (optional, e.g., WINC, MYPROJECT)
6. **GitHub organization filter** (optional, e.g., openshift, redhat)

Calculate date range from quarter:
- Q1: 01-01 to 03-31
- Q2: 04-01 to 06-30
- Q3: 07-01 to 09-30
- Q4: 10-01 to 12-31

**Store this information** for use in all subsequent phases.

---

### Phase 2: Data Collection and Cycle Time Analysis

#### Step 2.1: Fetch Jira Issues

```bash
# Fetch all issues created in the quarter
jira issue list \
  --jql "reporter = currentUser() AND created >= 'YYYY-MM-DD' AND created <= 'YYYY-MM-DD' AND project = PROJECT" \
  --paginate 500 \
  --plain \
  --columns KEY,SUMMARY,TYPE,STATUS,CREATED,RESOLVED,PRIORITY
```

**Parse the output:**
- Extract issue key, summary, type, status, created date, resolved date
- Calculate cycle time: (resolved_date - created_date) in days
- Filter for resolved/closed issues only

#### Step 2.2: Fetch GitHub PRs

```bash
# Search for merged PRs
gh api search/issues \
  -f q="author:USERNAME is:pr is:merged merged:YYYY-MM-DD..YYYY-MM-DD org:ORG" \
  --paginate \
  --jq '.items[] | {number, title, repository_url, closed_at, html_url}'
```

**For each PR**, fetch detailed info:

```bash
# Get PR creation and merge timestamps
gh pr view PR_NUMBER \
  --repo OWNER/REPO \
  --json number,title,createdAt,mergedAt,changedFiles,additions,deletions,url
```

**Calculate:**
- Cycle time: (mergedAt - createdAt) in days
- Total scope: files changed, lines added/deleted

#### Step 2.3: Analyze Cycle Times

Calculate statistics:

**Jira:**
- Total issues filed
- Total issues closed
- Closure rate: (closed / total) * 100
- Average cycle time for closed issues
- Longest 10 issues by cycle time

**GitHub:**
- Total PRs merged
- Average cycle time
- Longest 10 PRs by cycle time
- Total files changed (sum across all PRs)
- Total lines added/deleted

**Present findings:**

```markdown
## Q{quarter} {year} Cycle Time Analysis

### Jira Issues
- Total filed: X
- Total closed: Y (Z% closure rate)
- Average cycle time: A days

**Longest Jira Issues:**
1. PROJ-123: Summary (42 days) - Story
2. PROJ-456: Summary (38 days) - Task
...

### GitHub PRs
- Total merged: X
- Average cycle time: B days

**Longest GitHub PRs:**
1. owner/repo#123: Title (17 days, 37 files, +666 lines)
2. owner/repo#456: Title (8 days, 25 files, +1156 lines)
...
```

#### Step 2.4: Rank Achievements by Three Metrics

**Ranking 1: By Cycle Time (Longest Strategic Work)**
- Sort all items by cycle_days descending
- Top 10 = longest-running = likely strategic/foundational

**Ranking 2: By Impact (Infrastructure Keywords)**
- Base score = cycle_days
- Apply multipliers if title contains:
  - `infrastructure, foundational, framework, template, automation` → 1.5x
  - `release, backport, multi-, across, all` → 1.3x
  - `CI, test, workflow, pipeline` → 1.2x
- Sort by adjusted score descending

**Ranking 3: By Complexity (Scope)**
- For GitHub PRs: `(files_changed * 0.5) + (lines_added / 100)`
- For Jira: Use cycle_days as proxy
- Sort by score descending

**Cross-reference:**
- Items appearing in top 10 of multiple rankings = TOP ACHIEVEMENTS
- Present combined list with justification

**Example output:**

```markdown
## Top 5 Achievements (Cycle Time + Impact + Complexity)

1. **openshift/release#73920**: Add BYOH provisioning support (17 days, 37 files, +666 lines)
   - Top 5% longest PRs (cycle time)
   - Infrastructure keyword match (impact)
   - High scope (complexity)

2. **WINC-1573**: Update Core WINC Tests (63 days)
   - Longest Jira issue (cycle time)
   - Epic-level effort (complexity)

3. **openshift/release#75983**: Add AWS UPI jobs across 5 releases (8 days, 25 files, +1156 lines)
   - Multi-release keyword match (impact)
   - High scope (complexity)

...
```

---

### Phase 3: Achievement Narrative Refinement

For EACH of the top 5 achievements:

#### Step 3.1: Gather Detailed Context

**For GitHub PRs:**

```bash
# Get full PR details
gh pr view PR_NUMBER --repo OWNER/REPO \
  --json number,title,body,createdAt,mergedAt,changedFiles,additions,deletions,labels,commits

# Check for backports (multi-release indicator)
gh api "repos/OWNER/REPO/pulls/PR_NUMBER/commits" \
  --jq '.[].commit.message' | grep -i -E "(backport|cherry-pick|4\.[0-9]+)"
```

**Extract:**
- Files changed, lines added/deleted
- Multi-release indicators (backport commits, version labels)
- Related Jira tickets (from PR body)
- Time to merge (cycle time)
- Number of commits

**For Jira Issues:**

```bash
# Get issue details
jira issue view ISSUE_KEY --plain

# Check for linked PRs and sub-tasks
jira issue view ISSUE_KEY --plain | grep -E "(Pull Request|Sub-task|github.com)"
```

**Extract:**
- Issue type (Story, Task, Bug, Epic)
- Description (for WHAT/WHY context)
- Linked GitHub PRs
- Sub-tasks (indicates large effort)
- Time to resolve

#### Step 3.2: Apply Three Narrative Frameworks

For each achievement, write using the appropriate framework:

**Framework 1: Business Impact**

Emphasize:
- WHAT problem this solves for customers/users
- HOW this enables business objectives
- WHO benefits (team, customers, enterprise)
- WHY this matters strategically

**Template:**
```
I [delivered/enabled/built] [WHAT] by [HOW], [enabling/solving/creating] [BUSINESS_VALUE]. 
This work [spanned/involved] [SCOPE] over [DURATION]. [Strategic decision or approach]. 
[Production status and next steps enabled].
```

**Example:**
```
I delivered Phase 1 BYOH (Bring Your Own Host) provisioning support to Prow CI,
establishing foundational infrastructure that enables all future BYOH testing for
the Windows QE team. This was strategic infrastructure investment spanning 37 files
(+666 lines) over 17 days. I used a phased rollout strategy, starting with Azure
IPI and vSphere to de-risk deployment before expanding to other platforms. This
work is now running in production and directly enables Q2 Phase 2 work (WINC-1837).
```

**Framework 2: Technical Depth**

Emphasize:
- WHAT technical challenges were solved
- HOW you approached the problem (architecture, design)
- Technical complexity and scope
- Engineering rigor (testing, validation, deployment)

**Template:**
```
I [architected/engineered/refactored] [WHAT] by [TECHNICAL_APPROACH], [achieving/creating]
[TECHNICAL_OUTCOME]. [Scope details]. [Design decisions and trade-offs]. [Quality/rigor details].
```

**Example:**
```
I architected consolidation of 23 static YAML test files into 3 parameterized Go
templates (+1,280/-1,257 lines), building 11 resource code generators for
programmatic generation. The net +23 lines (after deleting 1,257) demonstrates
massive complexity reduction. Created single source of truth eliminating copy-paste
errors and enabling future OTE migration. This is technical debt reduction done right -
investing in architectural improvements that pay long-term dividends.
```

**Framework 3: Leadership**

Emphasize:
- HOW you influenced outcomes beyond code
- WHAT decisions you made and why
- WHO you helped or unblocked
- Strategic thinking and judgment calls

**Template:**
```
I [investigated/discovered/pivoted] [SITUATION], [made decision] to [ACTION], and
[documented/communicated/enabled] [KNOWLEDGE_SHARING]. [Technical justification].
[Outcome and team benefit].
```

**Example:**
```
I investigated AWS proxy configuration, discovered a bootstrap limitation where
Windows nodes can't reach external resources through proxy during initial setup
(before WMCO configures them), and made a strategic pivot to vSphere platform where
proxy works correctly. Rather than forcing a broken approach, I documented the
decision-making process in the PR description and leveraged proven patterns from
existing vsphere-proxy-e2e-operator job. Filled coverage gap in 6 days with working
solution, demonstrating engineering judgment and knowledge sharing.
```

#### Step 3.3: Choose Best Framework for Each Achievement

**Matching guide:**
- Infrastructure/foundational work → Business Impact or Technical Depth
- Problem-solving with pivots/decisions → Leadership
- Large refactors/architectural changes → Technical Depth
- Customer-facing features → Business Impact
- Cross-team collaboration → Leadership

Write 2-4 paragraphs per achievement combining:
- Lead paragraph: Refined narrative (200-300 words)
- Supporting details: Scope, duration, technical decisions
- Impact statement: Who benefits, what's enabled, strategic value

---

### Phase 4: Enhanced Report Generation

#### Step 4.1: Compile Full Statistics

From Phase 2 data, create comprehensive summary:

**Jira Section:**
- Total issues filed, closed, closure rate
- Breakdown by status (table format)
- Breakdown by type (table format)
- Average cycle time
- Top 5 longest issues with cycle times

**GitHub Section:**
- Total PRs merged
- Breakdown by repository (table format)
- Average cycle time
- Total files changed, lines added/deleted
- Top 5 longest PRs with cycle times and scope

**GitLab Section (if applicable):**
- Total MRs merged
- Breakdown by project

#### Step 4.2: Generate Enhanced Markdown Report

Create file: `~/Q{quarter}-{year}-Accomplishments-Enhanced.md`

**Structure:**

```markdown
# Q{quarter} {year} Quarterly Accomplishments
**[User's Name]** | [Team/Role]  
**Period:** {start_date} - {end_date}

---

## Executive Summary

**What I accomplished this quarter - ordered by strategic impact:**

1. [Top achievement 1 - one-line summary]
2. [Top achievement 2 - one-line summary]
3. [Top achievement 3 - one-line summary]
4. [Top achievement 4 - one-line summary]
5. [Top achievement 5 - one-line summary]

---

## Top Accomplishments - WHAT and HOW

### 1. [Achievement 1 Title] (PR #XXXXX or JIRA-KEY)

**WHAT I Accomplished:**
- [Bullet points on deliverables]
- Scope: X files changed, +Y lines
- Duration: Z days (start_date → end_date)
- Related Jira: KEY (if applicable)

**HOW I Accomplished It:**
- [Approach, architecture, design decisions]
- [Key technical choices]
- [Rollout strategy, risk management]
- [Production deployment status]

**Impact:**
- [Who benefits]
- [What it enables]
- [Strategic value]

**Why This Matters:**
[One paragraph explaining strategic importance]

---

[Repeat for achievements 2-5]

---

## By The Numbers - Q{quarter} {year}

| Metric | Achievement |
|--------|-------------|
| GitHub PRs Merged | X |
| Jira Issues Filed | Y |
| Jira Issues Closed | Z (W% closure rate) |
| Release Branches Supported | N |
| Platforms Tested | P |
| Average Cycle Time (Jira) | A days |
| Average Cycle Time (GitHub) | B days |
| Total Files Changed | F |
| Total Lines Added/Deleted | +L1/-L2 |

---

## How I Work - Key Themes

[Analyze patterns across top achievements:]

### 1. [Theme 1 - e.g., Strategic Decision-Making]
- [Examples from achievements]
- [Pattern description]

### 2. [Theme 2 - e.g., Fast Iteration]
- [Examples from achievements]
- [Pattern description]

### 3. [Theme 3 - e.g., Multi-Release Thinking]
- [Examples from achievements]
- [Pattern description]

---

## Cycle Time Analysis

### Jira Issues - Average: X days

**Longest issues (strategic work):**
1. [KEY]: [Summary] ([N days])
2. ...

### GitHub PRs - Average: Y days

**Longest PRs (foundational work):**
1. [repo#number]: [Title] ([N days, F files, +L lines])
2. ...

---

## Detailed Activity

### GitHub PRs by Repository

| Repository | Count | Notable PRs |
|------------|-------|-------------|
| repo1 | X | #123, #456 |
| repo2 | Y | #789 |

### Jira Issues by Type

| Type | Filed | Closed |
|------|-------|--------|
| Story | X | Y |
| Task | A | B |
| Bug | C | D |

---

**Generated:** {current_date}  
**Tool:** Quarterly Report Assistant  
**Data Sources:** Jira ({project}), GitHub ({org}), GitLab ({group})
```

#### Step 4.3: Present and Offer Enhancements

After generating the report:

1. **Confirm saved location**: `~/Q{quarter}-{year}-Accomplishments-Enhanced.md`
2. **Offer next steps:**
   - Refine specific sections further
   - Add more achievements beyond top 5
   - Generate shorter executive summary for Workday (4000 char limit)
   - Compare with previous quarter
   - Suggest goals for next quarter based on velocity

---

## Writing Style Guidelines

**Conversational, not robotic:**
- Write in first person ("I delivered", "I architected")
- Answer WHAT, HOW, WHY naturally in narrative flow
- Focus on decision-making and strategic thinking, not just activity

**Impact over activity:**
- ✅ "Enabled comprehensive Windows testing for enterprise customers"
- ❌ "Merged 25 PRs"

**Quantify where possible:**
- Cycle times (17 days, 8 days)
- Scope (37 files, +666 lines)
- Impact (5 releases, 60% time savings, 93 PRs)
- Team benefit ("Windows QE can now test BYOH scenarios")

**Be specific about HOW:**
- ✅ "Used phased rollout strategy starting with Azure IPI"
- ❌ "Deployed carefully"

---

## Troubleshooting

### CLI Not Authenticated

```bash
# Re-authenticate Jira
jira init

# Re-authenticate GitHub
gh auth refresh

# Re-authenticate GitLab
glab auth login
```

### No Data Returned

1. Verify authentication: `jira me`, `gh api user`
2. Check date format: YYYY-MM-DD
3. Try without filters first (no project/org)
4. Test platforms individually

### JQL Syntax Issues

If Jira query fails, try simpler JQL:
```bash
# Start simple
jira issue list --jql "reporter = currentUser()" --plain

# Add date filter
jira issue list --jql "reporter = currentUser() AND created >= '2026-01-01'" --plain

# Add project last
jira issue list --jql "reporter = currentUser() AND created >= '2026-01-01' AND project = PROJ" --plain
```

### GitHub Rate Limits

Check remaining quota:
```bash
gh api rate_limit
```

If rate limited (>5000 requests/hour), wait or continue tomorrow.

---

## Success Criteria

The workflow is successful when:

1. ✅ User has enhanced markdown report at `~/Q{quarter}-{year}-Accomplishments-Enhanced.md`
2. ✅ Top 5 achievements have polished WHAT/HOW/WHY narratives
3. ✅ Report includes cycle time analysis and "By The Numbers"
4. ✅ Report is ready for Workday with minimal editing
5. ✅ Process took ~30 minutes instead of 4-6 hours

---

## What This Workflow Does NOT Do

- ❌ Auto-submit reports to Workday or any system
- ❌ Make assumptions about what's "important" (user decides via ranking review)
- ❌ Fabricate context or achievements (uses only real data from CLI queries)
- ❌ Edit code or modify repositories
- ❌ Access private/confidential information beyond what CLI tools provide

---

## License

Apache License 2.0 - Part of Red Hat Community AI Tools
