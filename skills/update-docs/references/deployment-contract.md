# Deployment contract — `docs/deployment-contract.yaml`

Full mechanics for Step 4d. Like the other reconciles, it enumerates from the **whole codebase**, never from the pending diff — and never from the prose in `docs/deployment.md`, which is what it exists to replace as the machine-readable source.

## Why it exists

A GitOps drift audit compares what a repo says it needs against what the deployment manifests actually provide. When the only declaration is prose, two things go wrong and neither is visible from the repo:

- Any backticked `UPPER_SNAKE` token in the requirements section reads as a required variable, so a log-level *value* (`INFO`), an exit status (`SKIPPED`), or a named prefix (`DISPATCHER_`) is reported as missing config, week after week.
- Prose cannot say **optional**. An env var the deployment deliberately leaves at the app's own default is indistinguishable from one somebody forgot to set, so accepted defaults are re-flagged forever and the audit trains its reader to skip it.

The contract fixes both at the source: exact names, and an explicit `required` flag with the default beside it.

## Shape

```yaml
# docs/deployment-contract.yaml
kind: DeploymentContract
env:
  DISPATCHER_GITHUB_TOKEN:
    required: true
    description: GitHub PAT the poll loop authenticates with
  DISPATCHER_POLL_INTERVAL_S:
    required: false
    default: "60"
  TZ:
    required: false
    default: UTC
    description: container clock; the budget day boundary is DISPATCHER_TIMEZONE
resources:
  github-token:
    kind: Secret
  dispatcher-config:
    kind: ConfigMap
```

- `required: true` — the deployment MUST set it; absence is drift.
- `required: false` + `default:` — the app has a working default. State the default as the code has it; `null` is fine when the default is "unset".
- `resources:` — Secret/ConfigMap objects the manifest must provide, by object name.
- `description:` is optional and for humans; nothing parses it.

## Procedure

1. **Decide whether this repo needs one.** It does if the repo publishes a container image that something else deploys — a `Dockerfile` plus a CI publish step, or an existing `docs/deployment.md`. A library, a CLI, or a repo nothing deploys does **not** get one; note the skip in the Step 7 report.
2. **Enumerate every env var the code reads**, whole-tree, using the same rules as the env-example reconcile in `reconcile.md`. A settings object (pydantic `BaseSettings`, envconfig struct, a config module) is the authoritative list where one exists — it carries the default and the required-ness directly.
3. **Classify each one.** Required = no default in code, or the app fails to start without it. Optional = the code supplies a working default; record that default verbatim.
4. **List the resources** the deployment must supply: Secrets the app reads by object name, ConfigMaps it consumes via `envFrom`.
5. **Write or update the file.** Preserve existing ordering and comments; edit the entries that changed rather than regenerating the file.
6. **Never put a secret VALUE in it.** Same rule as the example env file — names, required-ness, and non-secret defaults only. A default that is itself a credential is recorded as `default: null` with a description.
7. **Keep `docs/deployment.md` as the prose companion.** The contract does not replace it — the doc explains *why* and *how*, the contract states *what*, and only the contract is parsed.

## The CI test is not optional

A contract that nobody checks is a doc with worse ergonomics: it rots exactly as fast, and now something downstream trusts it.

Where the repo has a settings object, add a test asserting the contract matches it — names, required-ness, and defaults — so a new setting fails CI until the contract is updated:

```python
# tests/test_deployment_contract.py
import yaml
from app.config import Settings

def test_contract_matches_settings():
    contract = yaml.safe_load(open("docs/deployment-contract.yaml"))["env"]
    for name, field in Settings.model_fields.items():
        key = name.upper()          # plus the settings' env_prefix, if it sets one
        assert key in contract, f"{key} missing from docs/deployment-contract.yaml"
        assert contract[key]["required"] is field.is_required()
```

Where there is no settings object, the enumeration in step 2 is the check, and it only happens when this skill runs. Say so in the Step 7 report rather than implying the file is verified.
