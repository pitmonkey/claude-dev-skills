# Local-path reconcile

Docs must not reference source files by absolute local filesystem path — those are meaningless off the author's machine and break the moment a directory moves. Scan the whole doc set and convert such references to stable forms.

## 1. Scan

Every doc file (`CLAUDE.md`, `README*`, `docs/**`) for absolute local paths: grep for `/home/`, `/Users/`, `/mnt/`, `/opt/`, leading `~/`, and Windows `C:\`-style paths.

## 2. Classify each hit and rewrite

**Inside the current repo** (path under `git rev-parse --show-toplevel`) → replace with the **repo-relative path** (e.g. `src/foo.py`). No URL needed.

**In another repo on disk** → derive the GitHub URL:

- repo root: `git -C <dir> rev-parse --show-toplevel`
- remote: `git -C <root> remote get-url origin`, normalise both `git@github.com:OWNER/REPO.git` and `https://github.com/OWNER/REPO.git` → `https://github.com/OWNER/REPO` (strip trailing `.git`)
- branch: `git -C <root> symbolic-ref --short refs/remotes/origin/HEAD` (strip the `origin/` prefix); fall back to `main`
- relative path = the full path minus the repo root
- build `https://github.com/OWNER/REPO/blob/<branch>/<relpath>` and swap it in, keeping the surrounding prose intact

**Not derivable** (target repo absent, or no GitHub remote) → leave the text unchanged and record it for the report.

## 3. Scope — stay conservative

Only rewrite prose references to source files. Paths inside fenced code blocks or example commands meant to be run locally are not doc references — skip those.
