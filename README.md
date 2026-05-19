# claude-dev-skills

Personal Claude Code skills plugin for dev workflows.

## Skills

| Skill | Description |
|-------|-------------|
| `claude-allows` | Add standard permissions to `.claude/settings.local.json` |
| `create-github-issue` | Capture a bug or problem from the current conversation as a GitHub issue |
| `generating-commit-messages` | Generate conventional commit messages |
| `grill-me` | Interview user relentlessly about a plan or design |
| `pr` | Push branch and open a GitHub pull request |
| `pr-review` | Fetch and review a GitHub PR, focused on dependency risk |
| `python-init` | Set up uv, pytest, ruff, mypy, pre-commit, CI for a Python project |
| `sc` | Stage and commit current changes, keeping docs updated |
| `update-docs` | Keep project documentation in sync with code changes |

## Install

Add this plugin via your marketplace or directly:

```
/plugin install pitmonkey/claude-dev-skills
```

## Development Setup

After cloning, activate the pre-commit hook (auto-increments patch version on each commit):

```
git config core.hooksPath .hooks
```
