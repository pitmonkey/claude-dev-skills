# Claude and Codex permission mapping

## Configuration concepts

| Claude entry | Codex mapping |
|---|---|
| `Bash(git status:*)` or simple `Bash(git status *)` | `pattern = ["git", "status"]`; choose the decision according to the requested policy |
| `Bash(gh pr:*)` | Split into the specific required `gh pr` subcommands; avoid granting every PR operation |
| `Bash(uv run:*)` | Broad code execution; prefer requested commands such as `["uv", "run", "pytest"]` |
| Complex quoted Bash patterns, pipelines, expansions, wildcards inside tokens | No automatic conversion; inspect actual argv and rule checker results |
| `Skill(...)` and skill `allowed-tools` | No direct command-rule equivalent; skill discovery/composition does not grant permission |
| `Read(...)`, `Edit(...)`, `Write(...)` | No direct command-prefix equivalent; inspect filesystem sandbox or permission-profile controls |
| `WebSearch` | Separate `web_search` configuration; no shell rule |
| `WebFetch(domain:...)` | Separate network controls; no direct one-to-one conversion |
| MCP tool names | Actual configured MCP server's enabled/disabled tool lists; connector tools may use separate app configuration |

Claude deny entries do not translate blindly into shell blocks. Codex `forbidden` prefix rules govern outside-sandbox requests, not universal filesystem exclusion. Preserve restrictions and report gaps.

## Bundled workflows

These are candidate command families, not an automatically installed allow list. Inspect each skill's actual invocation and select precise subcommands. Add needed flags or arguments to constrain a prefix where practical.

| Skill | Read candidates | Mutation / code-execution candidates (default `prompt`) |
|---|---|---|
| `sc` | `git status`, `git diff`, `git log`, `git branch --show-current` | `git add`, `git checkout -b`, `git commit`; documentation edits use host filesystem permissions |
| `generating-commit-messages` | `git diff --staged` | None; it does not commit |
| `pr` | `git remote get-url`, `git log`, `git diff`, `gh pr view`, `glab mr view`, forge auth status | `git push`, `gh pr create`, `glab mr create` |
| `gitgo` | Above plus `gh pr checks`, specific `glab api` GET endpoints | Above plus branch checkout, `git pull`, optional `git gone` (can force-delete branches) |
| `create-github-bug-issue`, `create-work-issue` | `gh issue view`, `gh label list`, repository reads | `gh issue create`, `gh issue edit`, `gh label create`; equivalent connector writes retain issue confirmation |
| `review-flagged-issues` | `gh issue list`, `gh issue view`, repository reads | `gh issue edit`, relevant label operations |
| `python-init` | Project inspection | `uv init`, `uv sync`, `uv add`, specific `uv run` checks, `pre-commit install` |
| `update-docs` | `git log`, `git diff`, `rg`, `wc` | Project-specific count/test commands; file edits use host permissions |
| `grill-me` | Repository inspection as needed | None required by the interview itself |
| `claude-allows` | Claude settings inspection | Writes Claude settings, not Codex permissions |
| `codex-allows` | Configuration inspection, `codex execpolicy check` | Writes requested rules/configuration; never auto-grants permissions to itself |

Compound shell commands may be split for matching; complex scripts can remain shell-wrapper invocations. Do not solve a mismatch by allowing the entire shell interpreter. Change to a direct argv command where possible or retain per-invocation approval.
