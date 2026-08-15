---
name: python-init
description: ONLY invoke when the user explicitly runs /python-init — do not auto-trigger for any other phrasing or context. Sets up uv, pytest, ruff, mypy, pre-commit, CI, .gitignore, config.py, README.md, and CLAUDE.md for a Python project.
---

# python-init

Initialise a Python project to the standard toolchain. **Never auto-trigger** — only run when the user explicitly invokes `/python-init`.

## Prerequisites

Check that the `python-pro` subagent is installed at `.claude/agents/python-pro.md` (project) or `~/.claude/agents/python-pro.md` (user). If neither exists, stop and tell the user:

> **python-pro subagent not found.** Install it before running `/python-init`. See your agent manager or add `.claude/agents/python-pro.md` manually.

Do not proceed until it is present.

---

## Detect mode

Check whether `pyproject.toml` exists in the current working directory:

- **Missing** → **New project mode** (full scaffold)
- **Present** → **Existing project mode** (audit + retrofit)

---

## New project mode

Run these steps in order:

1. If the project name is not obvious from the cwd, ask the user before proceeding.
2. Run `uv init` (if cwd is the project root) or `uv init <name>` (to create a subdirectory), then `uv sync`.
3. Add dev dependencies:
   ```bash
   uv add --dev pytest pytest-cov ruff mypy pre-commit
   ```
4. Append the following sections to `pyproject.toml` (do not overwrite existing content):
   ```toml
   [tool.pytest.ini_options]
   testpaths = ["tests"]
   addopts = "--cov=. --cov-report=term-missing"

   [tool.coverage.run]
   omit = ["tests/*", ".venv/*"]

   [tool.ruff]
   line-length = 100
   target-version = "py311"

   [tool.ruff.lint]
   select = ["E", "F", "I", "UP", "B", "SIM"]
   ignore = ["E501"]

   [tool.mypy]
   python_version = "3.11"
   strict = true
   ```
5. Create or update `.gitignore` — see template below.
6. Create `tests/__init__.py` (empty).
7. Create `config.py` — see template below.
8. Create `.env.example` — see template below.
9. Create `.pre-commit-config.yaml` — see template below.
10. Create `.github/workflows/ci.yml` — see template below.
11. Create `README.md` — see template below.
12. Create `CLAUDE.md` — see template below.
13. Run `pre-commit install`.
14. Run verification:
    ```bash
    uv run pytest
    uv run ruff check .
    uv run mypy .
    ```
    All three must pass (zero errors) before declaring done.

---

## Existing project mode

The primary goal is to standardise `CLAUDE.md` with task-planning guidance. Everything else is additive only.

1. Create or update `CLAUDE.md`:
   - If it doesn't exist, create it using the template below.
   - If it exists, add/replace the "How to plan and complete tasks" section; **preserve all other existing content**.
2. Audit for missing pieces and add only what is absent:
   - `pyproject.toml` tool sections (`[tool.pytest.ini_options]`, `[tool.coverage.run]`, `[tool.ruff]`, `[tool.mypy]`)
   - `.gitignore` (see template above)
   - `.pre-commit-config.yaml`
   - `.github/workflows/ci.yml`
   - `.env.example`
   - `config.py` (only if no env-loading file exists)
3. If any dev deps were missing, add them:
   ```bash
   uv add --dev pytest pytest-cov ruff mypy pre-commit
   pre-commit install
   ```
4. Run verification:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run mypy .
   ```

---

## File templates

### .gitignore
```
# Python-generated files
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Virtual environments
.venv

# Testing and coverage
.coverage
.coverage.*
.pytest_cache/
htmlcov/

# Type checking
.mypy_cache/
.dmypy.json
dmypy.json

# Linting
.ruff_cache/

# Environment files
.env
.env.local

# IDE and editor files
.idea/
.vscode/
*.sublime-project
*.sublime-workspace
*.swp
*.swo
*~

# OS files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Claude Code local settings
.claude/settings.local.json
.claude/agents/
```

### config.py
```python
import os

from dotenv import load_dotenv

load_dotenv()

# Required — will raise KeyError if missing and not DRY_RUN
DRY_RUN = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes")

if not DRY_RUN:
    WEBHOOK_URL = os.environ["WEBHOOK_URL"]
```

### .env.example
```
WEBHOOK_URL=https://example.com/webhook
DRY_RUN=false
```

### .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
```

### .github/workflows/ci.yml
Separate `test` and `lint` jobs. The `build` and `notify` jobs are project-specific — add them manually after scaffolding.

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6.0.2
      - uses: astral-sh/setup-uv@v8.0.0
      - run: uv sync
      - run: uv run pytest tests/ -v

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6.0.2
      - uses: astral-sh/setup-uv@v8.0.0
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run mypy .

# TODO: add project-specific build and notify jobs
```

### README.md
````markdown
# <project-name>

<Short description of what this project does.>

## Setup

```bash
cp .env.example .env   # fill in required values
uv sync
```

## Usage

```bash
uv run python main.py
DRY_RUN=true uv run python main.py  # skip side effects
```

## Development

```bash
uv run pytest          # tests
uv run ruff check .    # lint
uv run mypy .          # types
```
````

### CLAUDE.md
````markdown
# CLAUDE.md

## Project

<one-line description of what this project does>

## Commands

Setup, usage, and development commands are in `README.md` — read it rather than duplicating them here.

## Architecture

| File | Role |
|------|------|
| `main.py` | Entry point |
| `config.py` | Loads `.env` — exposes config vars |

## Code changes

All Python code changes must be handed off to the `python-pro` subagent. Do not write Python inline.
````
