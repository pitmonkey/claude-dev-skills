# Config & numeric-claim reconcile — procedures

Full mechanics for Step 4. Reconcile against the **whole codebase**, not the pending diff.

## Env-example reconcile

1. Enumerate **every** environment variable the code reads, across the whole tree — not just the current change:
   - Python: `os.getenv(...)`, `os.environ[...]`, `os.environ.get(...)`, and pydantic `BaseSettings` / `Settings` field names (env-mapped fields).
   - Node/TS: `process.env.X`.
   - Generic fallback: grep the source tree for env-access patterns for the language in use.
2. Locate the example env file — first of `.env.example`, `.env.sample`, `.env.template`. If none exists but the code reads env vars, note it in the report; do NOT create one unprompted.
3. Diff the read-set against the example file and **edit the example**:
   - Add every key the code reads that the example omits, with a placeholder value or comment (e.g. `LLM_API_KEY=` or `# LLM_API_KEY=<your key>`).
   - Flag keys in the example the code no longer reads (comment out or remove per the file's convention).
   - Preserve the file's existing grouping/order.
4. **Security — load-bearing:** NEVER write a real secret value into the example file. Keys and placeholders only. If you encounter a real value (in the environment or elsewhere), do not copy it in.

Adding only the current change's new keys is the exact bug this step exists to prevent: reconcile against the whole codebase every time.

## Numeric-claim re-derivation

Any documentation line stating a count *about the codebase* (most commonly a test count — "423 tests", "N tests passing") must be re-derived, not carried forward:

- Run the project's count command and read the result. Python: `pytest --collect-only -q` (use the trailing summary line for the collected count). Adapt per project type.
- Rewrite any stale number in `CLAUDE.md`, `README.md`, and other docs to the derived value.
- Scope: counts that are cheap to re-derive and drift silently (test counts). Not an open-ended audit of every number in the docs.

## Local-path reconcile

See `local-path-reconcile.md`.
