---
name: sap-cpi-gitops
description: "Work on this repository's SAP Cloud Integration iFlow source, manifests, CLI delivery, and GitHub Actions SDLC workflows; use when inspecting, changing, validating, or deploying repo-managed CPI content."
---

# SAP CPI GitOps

Use this skill for requests involving the SAP CPI flows, `cpi` CLI, manifests, GitHub Actions, or repository cleanup.

## Repository contract

- Treat `flows/<FLOW_ID>/` as the canonical editable source for an iFlow.
- Treat `config/<FLOW_ID>.yaml` as deployment metadata: package ID, artifact ID, name, version, source/template paths, and polling settings.
- Treat SAP-exported `.iflw` XML and bundle metadata as authoritative. Do not invent graphical iFlow designs from YAML or JSON.
- Preserve SAP IDs and symbolic names exactly. Use uppercase SAP-style directory, file, package, and artifact names unless an existing SAP export requires otherwise.
- Keep generated ZIPs under ignored `build/`; keep exported input artifacts under `artifacts/` only when a manifest explicitly references them.
- Never commit service keys, `.env` files, tokens, private keys, or tenant credentials.

## Required workflow

1. Inspect the relevant manifest, canonical flow directory, workflow, tests, and current Git status.
2. For imported CPI content, compare the SAP export with `flows/<FLOW_ID>` before editing. Migrate meaningful design/resources, not CPI-generated timestamps or line-ending-only changes.
3. Validate IDs, names, package references, version consistency, bundle symbolic name, and required source files.
4. Build with `scripts/build_iflow.py` and run the test suite before delivery.
5. Use `flow update` for an existing artifact and `flow upload` only for a new artifact ID. Save a new semantic version before deployment.
6. Verify the uploaded/saved bundle checksum before deployment.
7. Treat deployment as asynchronous: wait for CPI's terminal build/deploy status, fail on `FAIL`, `FAILED`, or `ERROR`, then require runtime status `STARTED`.
8. Check message-processing logs when the request is a smoke test or runtime verification.

## Mutation and safety boundaries

Read-only inspection is automatic. Before any CPI upload/update/version/deploy, Git commit/push, or deletion, require an explicit user request for that operation. Do not infer permission from a request to explain or review.

When a CPI operation fails:

- `401`/`403`: report authentication or role issues without exposing credentials.
- `404`: check the API-client service-key URL, package ID, and artifact ID.
- Lock errors: stop and ask the user to release the CPI editor lock; do not delete or overwrite unrelated content.
- Deployment task failure: report the task result and preserve the failure; retries are allowed only through the configured bounded workflow behavior.

## Documentation and handoff

Keep the canonical technical contract in `docs/specs/SAP_CPI_GITOPS_SPEC.md`. Update the relevant flow README or GitOps guide when behavior, commands, limitations, or source-of-truth rules change. Report changed files, validation results, and whether external mutations were performed.
