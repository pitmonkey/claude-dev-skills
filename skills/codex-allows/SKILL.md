---
name: codex-allows
description: Set up or audit Codex command permission rules for a repository, including mapping Claude allow lists and this plugin's skill workflows to Codex rules and configuration.
---

# Codex permissions

Manage repository-scoped Codex command rules, callable from Claude Code or Codex. Read [the mapping](references/permission-map.md) to choose permissions for the requested workflows. Creating this skill does not itself authorize changing a user's active permissions.

## Inspect and choose scope

Read the target repository's `.codex/config.toml`, `.codex/rules/*.rules`, and `.claude/settings.local.json` when present. Inspect user rules under `${CODEX_HOME:-$HOME/.codex}/rules/` and relevant managed restrictions when accessible, without printing credentials or unrelated configuration. Do not modify user or managed configuration unless explicitly requested. Default output is `.codex/rules/dev-skills.rules` in the target repository. Project rules load only for a trusted project; never mark a project trusted automatically.

Distinguish a fresh setup from an audit of existing rules. Preserve unrelated content and comments. Rules are Starlark, not JSON or executable Python: do not execute an existing rules file with Python or rewrite it with regular-expression substitutions. If a construct cannot be understood safely, leave it intact and report it.

## Prepare changes

For setup, select exact command prefixes from the mapping for the requested skills; do not install every permission merely because the plugin contains that skill. For a migration, translate only simple, understood Claude command prefixes. Mark unsupported entries as unmapped rather than guessing.

Use `allow` for requested read commands. Propose `prompt` for commands that modify repositories, publish, install dependencies, or execute project code; use `allow` for these only when the user's requested policy already authorizes unattended execution. Do not add blanket executable prefixes such as `git`, `gh`, `uv`, `bash -c`, or `python`. A prefix grants every suffix: e.g. `git commit` includes hook execution, and `uv run` can execute arbitrary project code. Never claim these are read-only permissions.

For audits, report `[add]`, `[modify]`, `[remove]`, `[annotated]`, and `[unmapped]`. Remove exact duplicate rules only when their entire meaning is identical. Broader and narrower rules are not interchangeable: the most restrictive matching decision wins. Preserve existing `prompt` and `forbidden` constraints. Show concrete proposed policy changes before applying; ask only for permission changes not already authorized by the user's request.

Keep explicit user retention decisions in a gitignored `.codex/codex-allows.json`, as `{ "keep": { "<exact rule text>": "reason" } }`. Retained entries are excluded from cleanup suggestions, but still report restrictions that prevent requested behavior. This sidecar is skill metadata, not Codex configuration.

## Write and validate

Use documented `prefix_rule` syntax, for example:

```python
prefix_rule(
    pattern = ["git", "status"],
    decision = "allow",
    match = ["git status --short"],
    not_match = ["git reset --hard"],
)
```

Validate in a temporary candidate file before replacing existing rules. If Codex CLI is installed, run `codex execpolicy check --pretty --rules <candidate> -- git status --short`, and corresponding positive/negative cases for each changed prefix. Include other discovered rule files with repeated `--rules` arguments to check conflicts. Never execute example mutation commands to test permission matching. If the checker is unavailable, report validation as incomplete rather than claiming the rules are active.

Do not change sandbox, network, approval policy, tool connections, or trust automatically as a side effect of mapping rules. If configuration changes are explicitly requested, verify supported keys against the installed Codex version and current official documentation; preserve existing permission profiles and do not mix `default_permissions` with legacy sandbox configuration.

Report files changed, resulting decisions, unmapped entries, conflicting restrictions, validation results, and the need to restart Codex. Explain that command rules govern requests outside the sandbox, not file access controls or skill-specific authorization.

Sources: [Codex rules](https://learn.chatgpt.com/docs/agent-configuration/rules) and [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference). Verify these when installed behavior differs; rules are experimental.
