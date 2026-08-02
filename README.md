# claude-dev-skills

Personal Claude Code skills plugin for dev workflows.

## Skills

| Skill | Description |
|-------|-------------|
| `claude-allows` | Add standard permissions to a new repo, or audit an existing `.claude/settings.local.json` (categorize, dedupe, prune one-offs) |
| `create-github-bug-issue` | Capture a bug or problem from the current conversation as a GitHub bug-report issue, flagging it `non-autonomous` when the fix needs a human |
| `create-work-issue` | Author a structured work-order issue for autonomous pickup by the github-dispatcher issue-worker, flagging it `non-autonomous` when the work needs a human |
| `generating-commit-messages` | Generate conventional commit messages |
| `gitgo` | Ship in one step: `sc` (docs+stage+commit) → `pr` (push+PR/MR, no confirm) → self-paced two-phase watch (confirms CI green, then swaps to main + pulls + sweeps the merged branch on merge). GitHub or GitLab |
| `grill-me` | Interview user relentlessly about a plan or design |
| `pr` | Push branch and open a pull request (GitHub) or merge request (GitLab) — forge auto-detected |
| `python-init` | Set up uv, pytest, ruff, mypy, pre-commit, CI for a Python project |
| `sc` | Stage and commit current changes, keeping docs updated |
| `update-docs` | Keep project documentation in sync with code changes |

### Issue labels

The two issue-creation skills apply markers; arming an issue for the autonomous worker stays a
human step.

| Label | Applied by | Meaning |
|-------|-----------|---------|
| `claude-drafted` | skill, always | Drafted by an issue-creation skill; awaiting human triage. Find them with `gh issue list --label claude-drafted` |
| `non-autonomous` | skill, when a trigger fires | The work needs a human — secrets, infra, pipelines, generated assets, third-party dashboards, aesthetic judgement. The issue body leads with a banner and a `## Human intervention required` list |
| `claude/pickup` | **human only** | Arms the issue for the github-dispatcher issue-worker (plan → test-first → PR). The skills never apply it, and never on a `non-autonomous` issue |

## Requirements

`pr` and `gitgo` shell out to the forge CLI for whichever remote the repo has — the forge
is detected automatically, so only the one you actually use needs to be installed:

| Remote | CLI | Auth |
|--------|-----|------|
| GitHub / GitHub Enterprise | [`gh`](https://cli.github.com) | `gh auth login` |
| GitLab (gitlab.com or self-hosted) | [`glab`](https://gitlab.com/gitlab-org/cli) | `glab auth login --hostname <host>` |

Authenticating once also makes detection faster and offline: the skills match the remote's
hostname against the hosts each CLI already knows before falling back to a network probe.

The issue skills (`create-github-bug-issue`, `create-work-issue`) are GitHub-only. They use
`gh` in a local terminal session. In a remote session (Claude Code on the web / phone, where
`CLAUDE_CODE_REMOTE=true`) the session proxy blocks repo-scoped `gh` writes with HTTP 403, so
both skills use the GitHub MCP tools (`mcp__github__*`) instead — no `gh` required there.

## Install

This repo is its own marketplace — register it, then install the plugin:

```
/plugin marketplace add pitmonkey/claude-dev-skills
/plugin install claude-dev-skills@claude-dev-skills
```

## Development Setup

After cloning, activate the pre-commit hook (auto-increments patch version on each commit):

```
git config core.hooksPath .hooks
```
