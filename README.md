# Azure DevOps Data Extraction Agent

A Python agent for extracting data from Azure DevOps via its REST API.  
Supports work items, build pipelines, release pipelines, Git repositories,  
commits, test plans, and test runs.  Results can be saved as **JSON** or **CSV**.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage – Python API](#usage--python-api)
- [Usage – CLI](#usage--cli)
- [Supported Data Sources](#supported-data-sources)
- [Project Structure](#project-structure)

---

## Prerequisites

- Python 3.8+
- An Azure DevOps organisation with a [Personal Access Token (PAT)][pat-docs]  
  that has at minimum the following scopes:
  - **Work Items** – `vso.work_read`
  - **Build** – `vso.build_read`
  - **Release** – `vso.release_read`
  - **Code** – `vso.code_read`
  - **Test Management** – `vso.test_read`

[pat-docs]: https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Configuration

The agent reads credentials from environment variables (or a `.env` file in the
project root):

| Variable | Description |
|---|---|
| `AZURE_DEVOPS_ORG_URL` | Full organisation URL, e.g. `https://dev.azure.com/my-org` |
| `AZURE_DEVOPS_PAT` | Personal Access Token |
| `AZURE_DEVOPS_PROJECT` | Default project name (optional) |
| `AZURE_DEVOPS_OUTPUT_DIR` | Output directory (default: `output`) |
| `AZURE_DEVOPS_OUTPUT_FORMAT` | `json` or `csv` (default: `json`) |

Create a `.env` file:

```dotenv
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/my-org
AZURE_DEVOPS_PAT=your_pat_here
AZURE_DEVOPS_PROJECT=MyProject
```

---

## Usage – Python API

```python
from azure_devops_agent import AzureDevOpsAgent, AgentConfig

config = AgentConfig(
    organization_url="https://dev.azure.com/my-org",
    personal_access_token="<PAT>",
    project="MyProject",
    output_dir="output",
    output_format="json",
)

agent = AzureDevOpsAgent(config)

# Extract active bugs
bugs = agent.extract_work_items(work_item_types=["Bug"], state="Active")

# Extract build runs on main
builds = agent.extract_builds(branch_name="refs/heads/main")

# Extract all repositories
repos = agent.extract_repositories()

# Extract commits from a specific repo
commits = agent.extract_commits(repository_id="my-repo", branch="main", top=200)

# Extract test plans
plans = agent.extract_test_plans()

# Extract everything in one call
all_data = agent.extract_all()
```

---

## Usage – CLI

```
python main.py [GLOBAL OPTIONS] COMMAND [COMMAND OPTIONS]
```

### Global options

| Flag | Description |
|---|---|
| `--org-url URL` | Organisation URL (overrides env var) |
| `--pat TOKEN` | Personal Access Token (overrides env var) |
| `--project NAME` | Default project (overrides env var) |
| `--output-dir DIR` | Output directory (default: `output`) |
| `--format {json,csv}` | Output format (default: `json`) |
| `--log-level LEVEL` | `DEBUG / INFO / WARNING / ERROR` (default: `INFO`) |

### Commands

#### `work-items`
```bash
# All work items in a project
python main.py work-items --project MyProject

# Filter by type and state
python main.py work-items --project MyProject --types Bug "User Story" --state Active

# Custom WIQL query
python main.py work-items --wiql "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = 'MyProject'"
```

#### `builds`
```bash
python main.py builds --project MyProject --branch refs/heads/main --top 50
```

#### `build-pipelines`
```bash
python main.py build-pipelines --project MyProject
```

#### `release-pipelines`
```bash
python main.py release-pipelines --project MyProject
```

#### `releases`
```bash
python main.py releases --project MyProject --top 100
```

#### `repositories`
```bash
python main.py repositories --project MyProject
```

#### `commits`
```bash
python main.py commits --project MyProject --repo-id my-repo --branch main --top 200
```

#### `test-plans`
```bash
python main.py test-plans --project MyProject
```

#### `test-runs`
```bash
# All runs
python main.py test-runs --project MyProject

# Automated only
python main.py test-runs --project MyProject --automated yes
```

#### `all`
```bash
# Extract everything and save as CSV
python main.py --format csv all --project MyProject
```

---

## Supported Data Sources

| Dataset | CLI command | Agent method |
|---|---|---|
| Work items | `work-items` | `extract_work_items` / `extract_work_items_by_wiql` |
| Build pipeline definitions | `build-pipelines` | `extract_build_pipelines` |
| Build runs | `builds` | `extract_builds` |
| Release pipeline definitions | `release-pipelines` | `extract_release_pipelines` |
| Release instances | `releases` | `extract_releases` |
| Git repositories | `repositories` | `extract_repositories` |
| Git commits | `commits` | `extract_commits` |
| Test plans | `test-plans` | `extract_test_plans` |
| Test runs | `test-runs` | `extract_test_runs` |

---

## Project Structure

```
azure_devops_agent/
├── __init__.py          # Package exports
├── agent.py             # AzureDevOpsAgent – high-level orchestrator
├── client.py            # Azure DevOps SDK connection factory
├── config.py            # AgentConfig – credentials & settings
├── output.py            # JSON / CSV serialisation helpers
└── extractors/
    ├── __init__.py
    ├── builds.py        # Build pipeline definitions & runs
    ├── pipelines.py     # Release pipeline definitions & instances
    ├── repositories.py  # Git repos, commits, branches
    ├── test_plans.py    # Test plans & test runs
    └── work_items.py    # Work items (WIQL)
main.py                  # CLI entry point
requirements.txt         # Python dependencies
```
