# SAP CPI project history

This file records project decisions and implementation milestones. Secrets and credential values are intentionally omitted.

## Current project

The project is focused on the four-step SAP Cloud Integration smoke-test workflow:

```text
Timer Start -> Content Modifier (Hello World!) -> Groovy Script (log payload)
-> Save and Deploy -> Monitor Message Processing
```

The active local manifest is `config/SAP_SMOKE_TEST.yaml`. It targets the existing editable package `poc` and flow ID `SAP_SMOKE_TEST_FLOW`.

## Delivery behavior

- `flow build` validates and copies an exported CPI flow artifact ZIP.
- `package create` creates a package only when a valid exported package ZIP is supplied.
- `flow upload` uploads the flow into the selected package.
- `flow version` saves the draft as the manifest version.
- `flow deploy` starts deployment and polls the build/deploy task.
- `flow status` and `list messages` verify runtime processing.

The CLI cannot generate SAP's proprietary iFlow ZIP format. The flow must be created in CPI, exported, and placed under `artifacts/` before delivery.
