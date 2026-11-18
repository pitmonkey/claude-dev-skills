# Create Work Issue — GitHub path and repo detection

Moved verbatim from this skill's `SKILL.md`, which points here at the step that needs it.

## Codex routing

In Codex, the Claude remote/local routing below does not apply: discover GitHub connector capabilities first and select that transport only if all required issue reads, writes, and label verification are supported; otherwise use authenticated `gh`. Select one transport before writing and keep it throughout. If neither is available, return the prepared draft and explain the missing capability. Keep existing dispatcher labels and confirmation/read-back requirements. In Claude remote sessions, retain the routing below and never fall back to `gh` writes.

## Pick the GitHub path

**First, pick the GitHub path.** This skill talks to GitHub two ways, and which one works
depends on where it runs. Detect it once, up front:

```bash
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] && echo remote || echo local
```

- **`remote`** — a web / phone / headless session (Claude Code on the web). The `gh` CLI
  **cannot** create issues here: the session's egress proxy serves `gh` only a narrow
  allowlist, and repo-scoped calls (`gh repo view`, `gh issue create`, `gh label ...`) come
  back **HTTP 403** ("GitHub access is not enabled for this session"). Use the **GitHub MCP
  tools** (`mcp__github__*`) instead — that is the sanctioned GitHub path in remote sessions.
- **`local`** — a local terminal session. Use the **`gh` CLI** as before; it authenticates
  with your `gh auth login` credentials.

Every mechanical step below gives the command for both paths. Run the whole flow on **one**
path — do not mix. The drafting steps (0, 2–5) are identical either way.

## Step 1 — Detect and confirm repo

If an `owner/repo` arg was given, use it. Otherwise detect the target repo:

- **remote (MCP):** `gh repo view` does **not** work here — the git remote points at the
  session proxy, not github.com. Parse owner/repo from the remote URL instead:

  ```bash
  git remote get-url origin | sed -E 's#\.git$##' | awk -F/ '{print $(NF-1)"/"$NF}'
  ```

- **local (gh):**

  ```bash
  gh repo view --json nameWithOwner --jq '.nameWithOwner'
  ```

Show the detected repo to the user and ask them to confirm before continuing.

If detection fails or returns nothing: stop and ask the user to provide the repo manually
(`owner/repo`). On the **local** path, if `gh` is not authenticated: stop and tell the user to
run `gh auth login`.
