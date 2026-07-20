# claude-dev-skills

Personal Claude Code skills plugin for dev workflows.

## Skills

| Skill | Description |
|-------|-------------|
| `claude-allows` | Add standard permissions to a new repo, or audit an existing `.claude/settings.local.json` (categorize, dedupe, prune one-offs) |
| `create-github-bug-issue` | Capture a bug or problem from the current conversation as a GitHub bug-report issue |
| `create-work-issue` | Author a structured work-order issue for autonomous pickup by the github-dispatcher issue-worker |
| `generating-commit-messages` | Generate conventional commit messages |
| `gitgo` | Ship in one step: `sc` (docs+stage+commit) → `pr` (push+PR/MR, no confirm) → self-paced two-phase watch (confirms CI green, then swaps to main + pulls + sweeps the merged branch on merge). GitHub or GitLab |
| `grill-me` | Interview user relentlessly about a plan or design |
| `pr` | Push branch and open a pull request (GitHub) or merge request (GitLab) — forge auto-detected |
| `python-init` | Set up uv, pytest, ruff, mypy, pre-commit, CI for a Python project |
| `sc` | Stage and commit current changes, keeping docs updated |
| `update-docs` | Keep project documentation in sync with code changes |

## Requirements

`pr` and `gitgo` shell out to the forge CLI for whichever remote the repo has — the forge
is detected automatically, so only the one you actually use needs to be installed:

| Remote | CLI | Auth |
|--------|-----|------|
| GitHub / GitHub Enterprise | [`gh`](https://cli.github.com) | `gh auth login` |
| GitLab (gitlab.com or self-hosted) | [`glab`](https://gitlab.com/gitlab-org/cli) | `glab auth login --hostname <host>` |

Authenticating once also makes detection faster and offline: the skills match the remote's
hostname against the hosts each CLI already knows before falling back to a network probe.

The issue skills (`create-github-bug-issue`, `create-work-issue`) are GitHub-only and always
require `gh`.

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
