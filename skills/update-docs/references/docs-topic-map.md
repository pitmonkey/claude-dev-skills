# docs/ topic map

Canonical destinations for task-specific content moved out of `CLAUDE.md`, with the reference line to leave behind in its place. Use the reference line instead of the full content — that is what keeps `CLAUDE.md` under the gate while the detail stays findable.

| Topic | File | Reference line |
|-------|------|-----------------|
| API conventions, request/response standards | `docs/api-standards.md` | `For API conventions, read docs/api-standards.md` |
| Testing framework setup, test patterns, fixtures | `docs/testing.md` | `For testing guidelines, read docs/testing.md` |
| Deployment procedures, environment config, infrastructure | `docs/deployment.md` | `For deployment rules, read docs/deployment.md` |
| Database schema, migrations, queries | `docs/database.md` | `For database schema and migrations, read docs/database.md` |
| Security policies, encryption, auth | `docs/security.md` | `For security policies, read docs/security.md` |
| Current architecture: components, boundaries, data flow | `docs/architecture.md` | `For system architecture, read docs/architecture.md` |
| Environment variables & secrets management | `docs/env-config.md` | `For environment setup and secrets, read docs/env-config.md` |
| Git workflows, CI/CD, branching strategy | `docs/ci-cd.md` | `For CI/CD and branching rules, read docs/ci-cd.md` |
| Monitoring, alerting, observability | `docs/observability.md` | `For monitoring and dashboards, read docs/observability.md` |
| Error handling standards, error codes | `docs/errors.md` | `For error handling patterns, read docs/errors.md` |
| Dependency management, version pins, upgrades | `docs/dependencies.md` | `For dependency policies, read docs/dependencies.md` |
| Development setup, local environment, IDE config | `docs/dev-setup.md` | `For local development setup, read docs/dev-setup.md` |
| Coding conventions, style, naming, code patterns | `docs/conventions.md` | `For coding conventions, read docs/conventions.md` |
| Runbooks, operational procedures, incident response | `docs/runbook.md` | `For operational runbooks, read docs/runbook.md` |
| Domain glossary, terminology, business rules | `docs/glossary.md` | `For domain terminology, read docs/glossary.md` |
| Third-party integrations, webhooks, external service contracts | `docs/integrations.md` | `For third-party integrations, read docs/integrations.md` |
| Frontend/UI component patterns, design system usage | `docs/frontend.md` | `For frontend patterns, read docs/frontend.md` |

If a project already uses a different filename for one of these topics, keep the project's name — match the repo, don't rename existing files to fit this table.

**Decision history is the git log.** Never create `docs/decisions.md`, a `docs/adr/` directory, or a "Decisions" section — why a choice was made lives in the commit that made it. If the repo already keeps a decision log, update it in place; don't seed one where none exists. `docs/architecture.md` describes the system as it is now, not how it got here.

If the content doesn't fit any row, invent a `docs/<topic>.md` in the same style rather than leaving it in `CLAUDE.md`.

**Core project files (`README.md`, `CLAUDE.md`) always stay at the root.** This table applies only to task-specific documentation.

When a topic in this table already has a file, check whether recent commits changed it and update the file — not just the reference line.
