---
name: gitgo
description: Use when the user wants to ship the current work end to end in one step — update docs, stage, commit, push, open a PR or MR, then watch it and switch back to main on merge. Triggered by /gitgo.
---

# Git Go (gitgo)

Ship current work in one command: `/sc` (update-docs + stage + commit) → `/pr`
(push + open PR/MR) → a self-paced two-phase watch that first confirms CI is green, then
switches to `main` and pulls once it merges. No mid-run confirmation — gitgo pushes
and opens the request on its own.

Works on GitHub and GitLab. `pr` detects which forge the remote is and reports it; gitgo
carries that answer into the watch loop and never re-detects.

This skill is an **orchestrator**. It does NOT re-implement staging, commit-message
generation, doc-sync, push, or PR-body logic — it invokes the existing `sc` and `pr`
skills so there is one source of truth. Run the steps in order; each gates the next.

## Process

### Step 1 — Stage + commit (invoke `sc`)

Invoke the `sc` skill via the Skill tool in **auto-branch mode**:

```
Skill({skill: "sc", args: "auto-branch"})
```

`sc` handles `update-docs`, explicit staging, and the commit. The `auto-branch` arg
tells `sc` to create a new branch **without prompting** when on `main`/`master` — gitgo
always needs a feature branch (Step 4 switches back to `main` on merge), so the y/n
question is skipped. On an existing feature branch `sc` just uses it.

- If `sc` stops because the working tree is clean **and** there are no commits ahead of
  the remote for this branch, there is nothing to ship — tell the user and STOP. Do not
  push an empty branch or arm a loop.
- If `sc` created a commit (or there were already unpushed commits), continue.

### Step 2 — Push + open PR/MR (invoke `pr`)

Invoke the `pr` skill via the Skill tool. It detects the forge, pushes the branch, and
creates the PR (GitHub) or MR (GitLab) with a generated title/body — reusing an existing
one if already open.

- **Fail-fast**: if the push is rejected or `gh pr create` / `glab mr create` errors, STOP
  here. Report the error. Do NOT arm the merge-watch — there is nothing to watch.
- Capture **both** the request number/URL and the forge `pr` detected; the loop needs both.

### Step 3 — Arm the merge-watch (invoke `loop`, dynamic)

Hand the watch to the `loop` skill via the Skill tool, self-paced (no interval), passing
the request number so it polls a concrete target. The watch runs in **two sequential
phases** — confirm CI is green, then wait for the merge. Use the prompt for the forge `pr`
detected in Step 2.

**GitHub:**

```
Skill({skill: "loop", args: "Watch PR #<N> in two phases.
Phase 1 (CI): run `gh pr checks <N>`. If it reports no checks exist, skip to Phase 2. If any check has FAILED, output FAILURE with the failing check names and STOP the loop — do not wait to merge. If checks are still pending/running, wait ~2 minutes and poll again. When every check has passed, output SUCCESS and continue to Phase 2.
Phase 2 (merge): poll PR #<N> every ~5 minutes until it merges; when merged, if the working tree is clean switch to main, git pull, then run `git gone` to delete the now-merged local feature branch, otherwise report the tree is dirty and do NOT switch. Stop the loop once handled."})
```

**GitLab:**

```
Skill({skill: "loop", args: "Watch MR !<N> in two phases. Read state with `glab api \"projects/:fullpath/merge_requests/<N>\"` — non-interactive JSON; never use a live/TUI view inside the loop.
Phase 1 (CI): read `head_pipeline.status`. If there is no head_pipeline, skip to Phase 2. If it is failed or canceled, output FAILURE with the pipeline URL and STOP the loop — do not wait to merge. If it is running, pending or created, wait ~2 minutes and poll again. When it is success or skipped, output SUCCESS and continue to Phase 2.
Phase 2 (merge): poll the same endpoint every ~5 minutes until `state` is merged; if `state` becomes closed, output CLOSED and STOP. When merged, if the working tree is clean switch to main, git pull, then run `git gone` to delete the now-merged local feature branch, otherwise report the tree is dirty and do NOT switch. Stop the loop once handled."})
```

- **Phase 1** is the ~2-minute CI gate. A red pipeline stops the loop and never advances
  to the merge wait — same fail-fast spirit as the push/PR step. A repo with no checks
  (`gh pr checks` reports none / no `head_pipeline`) falls straight through to Phase 2.
- **Phase 2** is the merge wait: it polls every ~5 minutes, self-stops the moment the
  request merges, then sweeps the
  merged branch with `git gone` (house convention — feature branches are disposable, only
  `main` is long-lived). `git gone` force-deletes locals whose upstream is `[gone]`; it
  needs the remote branch already deleted — on GitHub that is the repo's *auto-delete head
  branch on merge* setting, on GitLab the MR's *Delete source branch* option. If the alias
  is absent or the remote lingers, the sweep is a no-op and the stale branch is left for a
  manual `git gone` / `git branch -D`.
- `glab api` is used rather than `glab ci status` because the latter can open a live view;
  the API read is non-interactive and stable across `glab` versions.

Dynamic (self-paced) is deliberate over a fixed 5-minute cron: it decides its own cadence
and self-stops on a CI failure or once the PR merges. The loop is session-only — it dies
when this Claude session closes; for a watch that must survive that, use `/schedule`.

**Load-bearing guard — carry it into the loop prompt (above), scoped to Phase 2:** the
swap to `main` is destructive if the branch has uncommitted or new local work. The loop
MUST check `git status` is clean before `git checkout main && git pull && git gone`. If the
tree is dirty, it reports that and leaves the branch alone rather than stashing or
force-switching — and skips the `git gone` sweep too, since the branch was never left.

### Step 4 — Report

Confirm what's running: the commit hash, the PR URL, and that a self-paced two-phase watch
is armed — it confirms CI is green (printing SUCCESS or FAILURE) before waiting for the
merge, and stops itself on a CI failure or once the PR merges — sweeping the merged branch
with `git gone` on a clean tree. Remind the user it is session-only and how to stop it
early (cancel the loop / `CronDelete` if one was used).

## Rules

- **Forge is detected once, by `pr`** (its Step 0) — gitgo never re-detects and never mixes
  `gh` with `glab` in one run. It just carries `pr`'s answer into the loop prompt.
- **Compose, don't copy** — always invoke `sc`, `pr`, and `loop` rather than inlining
  their steps, so a fix in any of them flows through here.
- **Each step gates the next** — a clean tree stops before push; a failed push/PR stops
  before the loop; a failed CI check (Phase 1) stops before the merge wait. Never arm the
  watch unless a PR actually exists.
- **Push runs without a confirmation prompt** — shipping is the whole point of gitgo. The
  clean-tree stop (Step 1) and push/PR fail-fast (Step 2) are the guards, not a y/n.
- **Never force-push, never push to `main`/`master`, never auto-switch a dirty tree.**
- **No AI attribution** anywhere (commit trailer, PR body) — inherited from `sc`/`pr`.
- Interruptible: if any invoked skill asks the user something (PR body, etc.) or the user
  bails, honor it and stop — `/gitgo` is a macro, not an unstoppable pipeline. gitgo
  suppresses `sc`'s on-`main` branch question (Step 1 runs `sc` in `auto-branch` mode);
  the branch name itself is still auto-generated by `sc`.
