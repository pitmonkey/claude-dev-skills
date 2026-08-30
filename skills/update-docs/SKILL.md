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
- `wc -l CLAUDE.md README.md docs/*.md` — **record the CLAUDE.md count; Step 2 gates on it**
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

### The 200-line gate

CLAUDE.md loads on every task in the repo. Over-length means Claude pays context for content most tasks don't need, and the universal rules get lost in the noise. This gate is **measured, never estimated** — reading the file and judging it "about right" is the exact failure the gate exists to prevent.

1. Take the CLAUDE.md line count from Step 1's `wc -l`. If you skipped it, run it now.
2. **Under 200** — record the count for the Step 7 report and continue.
3. **200 or over** — splitting is **mandatory, not optional**:
   - Pick the largest task-specific sections — content about a specific domain (testing, deployment, database, security, a subsystem how-to) that doesn't apply to every task Claude does in this repo.
   - Move each one to its `docs/` file and leave the canonical reference line in its place. Destinations and reference lines: `references/docs-topic-map.md`.
   - Re-run `wc -l CLAUDE.md` and repeat until it is under 200.
4. If it is over 200 and genuinely nothing is task-specific enough to move, do **not** pass silently — say so explicitly in the Step 7 report, with the count and why.

**This does not conflict with "do not rewrite sections that are still accurate" above.** That rule governs *content*: don't reword what is still true. The gate governs *placement*: moving an accurate section verbatim into `docs/` is a move, not a rewrite. An accurate section is still a gate violation if it is task-specific and the file is over 200 lines.

A how-to that belongs to a topic another doc already owns is a split candidate at any length — see Ownership below.

### Ownership — one fact, one home

Every topic has exactly one owning file. Other files link to it; they never carry a copy.

| Topic | Owner | Everyone else |
|---|---|---|
| What the project is, requirements, install, run, test, build/release, contributing | `README.md` | link to it |
| Agent workflow, planning mandates, repo boundaries, conventions index, doc index | `CLAUDE.md` | — |
| Architecture, coding conventions, setup detail, testing detail, deployment | `docs/*.md` | one-line pointer from `CLAUDE.md` |

When the same fact appears in two files, **delete it from the non-owner and leave a pointer**. Never resolve an overlap by copying, and never by editing both copies to agree — the second copy is the defect, not its staleness.

Two directions, both enforced:
- CLAUDE.md must not restate README content (install steps, run instructions, feature blurbs).
- README must not carry internal/implementation detail that belongs in CLAUDE.md or `docs/`.

Checking is cheap: diff the section headings of README.md and CLAUDE.md against each other and against `docs/*.md`. Matching or near-matching headings are where duplication hides.

Common things to check based on project type:
- **Services/dependencies**: version bumps, new services added, services removed
- **Config/environment**: new env vars, changed defaults, new secrets
- **Known issues**: items that are now resolved; new issues discovered
- **Conventions**: new patterns established in recent commits

## Step 3 — Update README.md and supplementary docs (if they exist)

Update only what has changed. Match the existing structure and tone exactly.

**README is for humans, not agents.** It answers, and only answers:
- What the project is
- What is required to run it
- How to install it
- How to run it
- How to test it
- How to build/release it
- How to contribute

Keep each at pointer depth — detail lives in `docs/`, per the ownership table. Update version numbers, feature lists, or setup instructions that are now stale.

**Eviction rule:** agent-oriented content found in README — skill invocations, planning mandates, internal conventions, subsystem implementation notes — does not belong there. Move it to `CLAUDE.md` or `docs/` per the ownership table, don't just leave it.

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

Four reconciles, each whole-codebase, not diff-local. **Read `references/reconcile.md` for the procedures before running them** — the enumeration rules are what make these work.

- **4a — Env-example.** Enumerate every env var the code reads across the whole tree, diff against `.env.example` (or `.sample`/`.template`), and edit the example. Adding only the current change's new keys is the exact bug this step prevents. **Security — load-bearing: NEVER write a real secret value into the example file.** Keys and placeholders only.
- **4b — Numeric claims.** Any count *about the codebase* ("423 tests") is re-derived by running the project's count command, never carried forward.
- **4c — Local paths.** Convert same-repo references to repo-relative paths and other-repo references to GitHub URLs; flag what can't be derived for the Step 7 report. Procedure: `references/local-path-reconcile.md`.
- **4d — Deployment contract.** If the repo publishes a deployed image, write or update `docs/deployment-contract.yaml` — the machine-readable list of env vars and Secret/ConfigMap objects the deployment must provide, each marked `required: true` or `required: false` with its default. Enumerate from the code, never from the prose in `docs/deployment.md`. Procedure and schema: `references/deployment-contract.md`. **Same secret rule as 4a — names and non-secret defaults only, never a value.**

## Step 5 — Formatting hygiene

Applies to each doc file this run **already touched**. This is not a repo-wide reformat sweep, and untouched files stay untouched.

- No runs of 2+ consecutive blank lines; no whitespace-only lines; no trailing whitespace.
- **Do not hard-wrap Markdown prose.** One line per paragraph — editors and viewers soft-wrap already. Hard wrapping buys nothing, inflates the line count the Step 2 gate measures, and turns a one-word edit into a multi-line reflow diff. Bullets and table rows are single lines too, however long.
- **Never reflow a file just to change its wrap style.** If existing prose is already hard-wrapped, leave it — rewrapping the whole file to satisfy this rule is exactly the diff noise the rule exists to avoid. Write new and edited paragraphs unwrapped; let the file converge as it is edited.
- Never touch fenced code blocks or URLs.

## Step 6 — Update todo / work-tracking file (if it exists)

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

## Step 7 — Report

Briefly summarise what was changed in each file and why. Note anything skipped and why (e.g. "No README found").
- **CLAUDE.md gate:** state the line count before and after, and whether it passed or forced a split. Always state the number — "looked fine" is not a report.
- **Sections moved:** each section moved out of CLAUDE.md, with its `docs/` destination.
- **Duplication resolved:** each overlap found, which file kept ownership, which lost the copy.
- Env-example reconcile: list env keys added/flagged and the example file touched, or why skipped (e.g. "no example env file found").
- Numeric-claim re-derivation: list any numeric claims corrected (old → new), or why skipped (e.g. "no numeric claims in docs").
- Local-path reconcile: list paths converted to GitHub URLs (old → new), and any local paths flagged but left as-is because the target repo/remote could not be resolved.
- Deployment contract: entries added/changed/removed in `docs/deployment-contract.yaml`, whether a CI test now checks it against a settings object, or why the repo was skipped (e.g. "library, nothing deploys it").

## Common Mistakes

**The 200-line gate is measured, not estimated.** Run `wc -l CLAUDE.md`. Reading the file and judging it "about right" is how a 900-line CLAUDE.md sails through a clean report. If the number is 200 or over, splitting is mandatory — not a suggestion to weigh.

**Never resolve duplication by copying.** One owner, pointers everywhere else. Editing both copies so they agree leaves the defect in place — the second copy *is* the defect.

**README is for humans.** Skill invocations, agent workflow mandates, and internal conventions belong in CLAUDE.md or `docs/`, however accurate they are.

**Docs describe the present, not the past.** `docs/architecture.md` says what the system *is now* — components, boundaries, data flow. It is not a decision log. Why a choice was made lives in the commit that made it, so don't restate rationale in docs, don't append a "Decisions" section to a file that has none, and never seed `docs/decisions.md` or a `docs/adr/` directory. A repo that already keeps a decision log is the exception: update it in place. When content is superseded, rewrite it where it stands rather than layering a new section beside the old one.

**Don't hard-wrap Markdown, and don't rewrap what's already there.** New prose goes on one line per paragraph; existing wrapped prose is left alone until it is edited anyway. Reflowing a file for style is a diff-noise change with no reader benefit.

**`docs/` matters too — CLAUDE.md and README.md are not the whole job.** If a `docs/` directory exists, it must be checked. Deployment guides, runbooks, and architecture docs drift just as fast and are often more operationally critical.

**Don't skip `docs/` because nothing looks obviously stale.** Check it against the git log — env var additions, config changes, and new deployment steps are easy to miss without an explicit cross-reference.

**Deployment docs always live in `docs/deployment.md`, never at the root — and if a Dockerfile exists, that file must exist.** Create it if missing; Docker presence is a deployment signal and the guide is not optional.

**CI/CD changes almost always mean deployment docs are stale.** If `.github/workflows/`, `Dockerfile`, `docker-compose.yml`, or similar files changed in recent commits, treat that as a mandatory trigger to review deployment docs — even if the change looks minor (e.g. adding a new runner or changing a build flag).

**`.env.example` reconcile is whole-codebase, not diff-local**, and **never write real secret values into it** — keys and placeholders only, even if a real value is visible in the environment.

**A deployment contract without `required: false` entries is the failure mode, not the win.** The point of the file is that it can say "optional, and here is the default" — which prose cannot. Marking everything required just relocates the noise, and every accepted default gets re-flagged by whatever consumes it.

**Don't write a contract the repo cannot check.** Where a settings object exists, the contract ships with the test that asserts they agree; otherwise say plainly in the report that nothing verifies it between runs of this skill.

**Don't hard-code local filesystem paths in docs.** A path like `/home/user/git/other-repo/src/x.py` is meaningless off the author's machine and breaks when anything moves. Reference same-repo files by repo-relative path, and files in other repos by GitHub URL. If the URL can't be derived, flag it in the report rather than leaving a broken local path silently in place.
