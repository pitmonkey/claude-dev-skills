---
name: update-docs
description: Use when project state has changed — new features, config, env vars, dependencies, deployment changes — and documentation may have drifted from what the code actually does
allowed-tools: [Read, Edit, Write, Glob, Grep, Bash]
---

# Update Docs

Keep project documentation in sync with the current codebase. Do all steps in order.

## Step 1 — Gather context

Run these in parallel:
- `git log --oneline -20` — recent commits
- `git diff HEAD` — uncommitted changes (may be empty if just committed)
- Read `CLAUDE.md`
- Check for README: `README.md`, `README.rst`, `README.txt` (read whichever exists)
- Check for deployment docs: `docs/deployment.md` (read if found)
- Check for a todo/work-tracking file: look for `scratch/todo.md`, `TODO.md` (read if found)
- Check for a changelog: `CHANGELOG.md`, `CHANGELOG` (read if found — note: changelog is release history, not a task list; update separately from todos)
- Check for a `docs/` directory — list its contents; also check for `docs/deployment.md` explicitly and read it if it exists

Then probe the project structure to understand what kind of project this is:
- Look for `package.json`, `go.mod`, `Cargo.toml`, `pyproject.toml`, `project.godot`, etc.
- Check for CI/CD and deployment artefacts: `.github/workflows/`, `.gitlab-ci.yml`, `Dockerfile`, `docker-compose.yml`, `kubernetes/`, `k8s/`, `helm/` — changes here are a strong signal that deployment docs are stale
- Skim the top-level directory layout
- This determines what to focus on in subsequent steps

## Step 2 — Update CLAUDE.md

Update only what has changed since the last sync. Do not rewrite sections that are still accurate.

Guiding principles:
- Match the existing CLAUDE.md structure — don't add sections that aren't there, don't rename ones that are
- For tables (services, dependencies, config values): update rows where data changed, add new rows, remove deleted ones
- For prose sections (notes, patterns, known issues): update statements that are now outdated; mark completed items as done
- Keep it concise — CLAUDE.md is a reference for the AI, not a changelog

### Reference Patterns (Best Practices)

**CLAUDE.md bloat:** If CLAUDE.md grows beyond ~250 lines, it's a signal to move task-specific content into separate `docs/` files. Bloated CLAUDE.md means:
- Claude loads unnecessary context for every task
- Core universal information gets lost in noise
- Future documentation updates are harder to find

When updating CLAUDE.md, look for sections that could move to `docs/` — especially content about specific domains (testing, deployment, database, security) that don't apply to every task Claude does in the repo.

Structure CLAUDE.md by moving task-specific topics into `docs/` with reference lines. This keeps CLAUDE.md focused on universal context and lets Claude load task-specific details only when needed.

Common patterns:

| Topic | File | Reference Line |
|-------|------|-----------------|
| API conventions, request/response standards | `docs/api-standards.md` | `For API conventions, read docs/api-standards.md` |
| Testing framework setup, test patterns, fixtures | `docs/testing.md` | `For testing guidelines, read docs/testing.md` |
| Deployment procedures, environment config, infrastructure | `docs/deployment.md` | `For deployment rules, read docs/deployment.md` |
| Database schema, migrations, queries | `docs/database.md` | `For database schema and migrations, read docs/database.md` |
| Security policies, encryption, auth | `docs/security.md` | `For security policies, read docs/security.md` |
| Architecture decisions, trade-offs | `docs/architecture.md` | `For architecture decisions, read docs/architecture.md` |
| Environment variables & secrets management | `docs/env-config.md` | `For environment setup and secrets, read docs/env-config.md` |
| Git workflows, CI/CD, branching strategy | `docs/ci-cd.md` | `For CI/CD and branching rules, read docs/ci-cd.md` |
| Monitoring, alerting, observability | `docs/observability.md` | `For monitoring and dashboards, read docs/observability.md` |
| Error handling standards, error codes | `docs/errors.md` | `For error handling patterns, read docs/errors.md` |
| Dependency management, version pins, upgrades | `docs/dependencies.md` | `For dependency policies, read docs/dependencies.md` |
| Development setup, local environment, IDE config | `docs/dev-setup.md` | `For local development setup, read docs/dev-setup.md` |

Use reference lines instead of full content. When updating CLAUDE.md, check if these docs exist and update them if any referenced topics changed in recent commits.

**Note:** Core project files (`README.md`, `CLAUDE.md`) always stay at the root. The "always in docs/" rule applies only to task-specific documentation (testing, deployment, database, security, etc.).

Common things to check based on project type:
- **Services/dependencies**: version bumps, new services added, services removed
- **Config/environment**: new env vars, changed defaults, new secrets
- **Known issues**: items that are now resolved; new issues discovered
- **Conventions**: new patterns established in recent commits

## Step 3 — Update README.md and supplementary docs (if they exist)

Update only what has changed. README is user/contributor-facing — keep it high-level.
- Match the existing structure and tone exactly
- Update version numbers, feature lists, or setup instructions that are now stale
- Do not add internal/implementation details that belong in CLAUDE.md

### Deployment docs (docs/deployment.md)

Deployment docs always live in `docs/deployment.md`. These drift fastest. Cross-reference against the git log and CI/CD artefacts from Step 1. Update if any of the following changed:
- CI/CD pipeline steps, runner names, or build strategy (e.g. matrix builds, new runners)
- Container registry, image names, or tagging scheme
- Environment variables or secrets required at deploy time
- Deployment targets, clusters, or namespaces
- Build tooling (e.g. switching from Docker BuildKit single-platform to multi-arch manifest merge)
- Rollback or release procedures

### Other docs/ files

For each file found in `docs/` (from Step 1): update sections that reference things changed in recent commits — env vars, config, deployment steps, architecture, runbook commands, etc. Apply the same "update only what changed" discipline.

If no README and no `docs/` exist, skip this step.

## Step 4 — Config & numeric-claim reconcile

Reconcile machine-checkable facts against the **whole codebase**, not the pending
diff. Edit files to match reality, exactly as the earlier steps edit docs.

### 4a — Env-example reconcile (whole-codebase, not diff-local)

1. Enumerate **every** environment variable the code reads, across the whole tree —
   not just the current change:
   - Python: `os.getenv(...)`, `os.environ[...]`, `os.environ.get(...)`, and pydantic
     `BaseSettings` / `Settings` field names (env-mapped fields).
   - Node/TS: `process.env.X`.
   - Generic fallback: grep the source tree for env-access patterns for the language
     in use.
2. Locate the example env file — first of `.env.example`, `.env.sample`,
   `.env.template`. If none exists but the code reads env vars, note it in the report;
   do NOT create one unprompted.
3. Diff the read-set against the example file and **edit the example**:
   - Add every key the code reads that the example omits, with a placeholder value or
     comment (e.g. `LLM_API_KEY=` or `# LLM_API_KEY=<your key>`).
   - Flag keys in the example the code no longer reads (comment out or remove per the
     file's convention).
   - Preserve the file's existing grouping/order.
4. **Security — load-bearing:** NEVER write a real secret value into the example file.
   Keys and placeholders only. If you encounter a real value (in the environment or
   elsewhere), do not copy it in.

Adding only the current change's new keys is the exact bug this step exists to prevent:
reconcile against the whole codebase every time.

### 4b — Numeric-claim re-derivation

Any documentation line stating a count *about the codebase* (most commonly a test
count — "423 tests", "N tests passing") must be re-derived, not carried forward:

- Run the project's count command and read the result. Python: `pytest --collect-only -q`
  (use the trailing summary line for the collected count). Adapt per project type.
- Rewrite any stale number in `CLAUDE.md`, `README.md`, and other docs to the derived
  value.
- Scope: counts that are cheap to re-derive and drift silently (test counts). Not an
  open-ended audit of every number in the docs.

### 4c — Local-path reconcile (link to GitHub, don't hard-code local paths)

Docs must not reference source files by absolute local filesystem path — those are
meaningless off the author's machine and break the moment a directory moves. Scan the
whole doc set and convert such references to stable forms.

1. **Scan** every doc file (`CLAUDE.md`, `README*`, `docs/**`) for absolute local
   paths: grep for `/home/`, `/Users/`, `/mnt/`, `/opt/`, leading `~/`, and Windows
   `C:\`-style paths.
2. **Classify each hit and rewrite:**
   - **Inside the current repo** (path under `git rev-parse --show-toplevel`) → replace
     with the **repo-relative path** (e.g. `src/foo.py`). No URL needed.
   - **In another repo on disk** → derive the GitHub URL:
     - repo root: `git -C <dir> rev-parse --show-toplevel`
     - remote: `git -C <root> remote get-url origin`, normalise both
       `git@github.com:OWNER/REPO.git` and `https://github.com/OWNER/REPO.git` →
       `https://github.com/OWNER/REPO` (strip trailing `.git`)
     - branch: `git -C <root> symbolic-ref --short refs/remotes/origin/HEAD` (strip the
       `origin/` prefix); fall back to `main`
     - relative path = the full path minus the repo root
     - build `https://github.com/OWNER/REPO/blob/<branch>/<relpath>` and swap it in,
       keeping the surrounding prose intact.
   - **Not derivable** (target repo absent, or no GitHub remote) → leave the text
     unchanged and record it for the Step 6 report.
3. **Scope — stay conservative:** only rewrite prose references to source files. Paths
   inside fenced code blocks or example commands meant to be run locally are not doc
   references — skip those.

## Step 5 — Update todo / work-tracking file (if it exists)

- **Mark completed items** — anything finished in recent commits (check git log from Step 1)
- **Add new items** — known remaining work, bugs, or inline TODOs found in code
- **Remove or update** stale items that no longer apply
- Grep for inline TODOs in source code (adapt pattern to the project's language and directory structure):
  - `grep -rn "TODO\|FIXME\|HACK\|@todo" <src_dir>/` — adjust `<src_dir>` to the actual source root
- If no todo file exists, skip this step (do not create one unprompted)

If a `CHANGELOG.md` was found in Step 1, update it separately — it is release history, not a task list:
- Add an entry for any notable changes in recent commits (new features, breaking changes, significant fixes)
- Follow the existing format exactly (e.g. Keep a Changelog, date-prefixed, etc.)
- Do not add entries for chore/refactor commits unless the project's changelog convention includes them

## Step 6 — Report

Briefly summarise what was changed in each file and why. Note anything skipped and why (e.g. "No README found").
- Env-example reconcile: list env keys added/flagged and the example file touched, or why skipped (e.g. "no example env file found").
- Numeric-claim re-derivation: list any numeric claims corrected (old → new), or why skipped (e.g. "no numeric claims in docs").
- Local-path reconcile: list paths converted to GitHub URLs (old → new), and any local paths flagged but left as-is because the target repo/remote could not be resolved.

## Common Mistakes

**Don't stop at CLAUDE.md and README.md.** If a `docs/` directory exists, it must be checked — updating those two files is not sufficient. Deployment guides, runbooks, and architecture docs drift just as fast and are often more operationally critical.

**Don't skip `docs/` because nothing looks obviously stale.** Check it against the git log — env var additions, config changes, and new deployment steps are easy to miss without an explicit cross-reference.

**Deployment docs always live in `docs/deployment.md`.** Never at the root. If a repo has Docker, it must have `docs/deployment.md` — this is not optional.

**CI/CD changes almost always mean deployment docs are stale.** If `.github/workflows/`, `Dockerfile`, `docker-compose.yml`, or similar files changed in recent commits, treat that as a mandatory trigger to review deployment docs — even if the change looks minor (e.g. adding a new runner or changing a build flag).

**If a Dockerfile exists, `docs/deployment.md` must exist.** Any repo with Docker containers must have `docs/deployment.md`. If missing, create it. Docker presence is a deployment signal — the guide is not optional.

**`.env.example` reconcile is whole-codebase, not diff-local.** Adding only the current
change's new keys is the exact drift this step exists to prevent — enumerate every env
var the code reads across the whole tree and reconcile the full set.

**Never write real secret values into an example env file.** Keys and placeholders
only, even if a real value is visible in the environment.

**Don't hard-code local filesystem paths in docs.** A path like
`/home/user/git/other-repo/src/x.py` is meaningless off the author's machine and breaks
when anything moves. Reference same-repo files by repo-relative path, and files in other
repos by GitHub URL (`https://github.com/OWNER/REPO/blob/<branch>/<path>`). If the URL
can't be derived, flag it in the report rather than leaving a broken local path silently
in place.
