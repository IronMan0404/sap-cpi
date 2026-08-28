# SAP Cloud Integration GitOps

## What this repository manages

This repository manages the delivery lifecycle of an SAP Cloud Integration artifact:

```text
SAP-exported iFlow ZIP → Git → build validation → CPI API update/upload
→ save version → deploy → runtime/message verification
```

The YAML manifest stores deployment metadata such as package ID, flow ID, version, and file paths. It is not an alternative iFlow design language.

## Source of truth

The actual flow design is the SAP-exported integration project archive. For the smoke test, it must contain:

```text
Timer Start Event → Content Modifier (Hello World!) → Groovy Script (log payload)
```

Create or model this flow in SAP Cloud Integration, or use SAP’s GitHub integration to import/pull it. Export/sync the resulting archive to `artifacts/SAP_SMOKE_TEST_FLOW.zip`. Store Groovy scripts and other resources in the exported project as provided by SAP.

VS Code and Cursor are useful for reviewing the archive, editing Groovy/resources, changing manifests, and reviewing pull requests. They are not SAP’s graphical iFlow editor and cannot reliably generate the complete SAP bundle from YAML or JSON.

## Local deployment into existing package

The active manifest targets package `poc` and flow `SAP_SMOKE_TEST_FLOW`:

```powershell
cpi.exe --key-file .\CPI-API-KEY.json flow pull --manifest .\config\SAP_SMOKE_TEST.yaml --version active
cpi.exe flow build --manifest .\config\SAP_SMOKE_TEST.yaml --output .\build\SAP_SMOKE_TEST_FLOW.zip
cpi.exe --key-file .\CPI-API-KEY.json flow update --manifest .\config\SAP_SMOKE_TEST.yaml --bundle .\build\SAP_SMOKE_TEST_FLOW.zip --apply
cpi.exe --key-file .\CPI-API-KEY.json flow version --manifest .\config\SAP_SMOKE_TEST.yaml --apply
cpi.exe --key-file .\CPI-API-KEY.json flow deploy --manifest .\config\SAP_SMOKE_TEST.yaml --apply
cpi.exe --key-file .\CPI-API-KEY.json flow status --id SAP_SMOKE_TEST_FLOW
```

`flow pull` downloads the active artifact from CPI to the manifest’s flow-template path. Pull before reviewing or changing a flow in Git. If the artifact is locked in the CPI editor, `flow update` is rejected until the editor lock is released; deployment of an already-versioned active artifact can still proceed.

Use `flow upload` instead of `flow update` when the artifact ID does not yet exist in the package. `flow update` uses SAP’s active-artifact PUT operation and replaces the existing draft content.

## GitHub Actions

The workflow at `.github/workflows/deploy-sap-cpi.yml` runs on demand or when the flow source/configuration changes. Pushes default to `update` for the existing artifact. Manual runs offer three operations:

- `update`: replace the existing draft, save a version, and deploy. The CPI editor lock must be released.
- `upload`: create a new artifact ID, save a version, and deploy.
- `deploy-only`: deploy the existing active version without changing its draft. Use this when the artifact is locked or when no local content change is intended.

Create a GitHub Actions secret named `CPI_SERVICE_KEY_JSON` containing the complete API-client service-key JSON. Never commit the key, print it, or put it in logs. The workflow writes it only to a temporary runner file and removes that file at the end.

The service key must belong to a Process Integration Runtime `api` service instance with the roles required to update, version, deploy, and read runtime status.

## Package choices

- Existing package: set `package.id: poc` and skip package creation.
- New package: use `config/SAP_SMOKE_TEST_CREATE_PACKAGE.yaml` and provide `artifacts/SAP_SMOKE_TEST_PACKAGE.zip`, then run `package create --apply` before uploading the flow.

## Limitations and safety

- YAML/JSON does not generate SAP iFlow shapes.
- A valid SAP-exported ZIP is required; the placeholder ZIP is not the smoke-test design.
- `flow upload` creates an artifact and can fail if the ID already exists; use `flow update` for an existing artifact.
- The CLI does not automatically delete or undeploy artifacts.
- Externalized parameters, credentials, certificates, keystores, and other tenant configuration may need separate deployment/configuration.
- Deployment is asynchronous. A successful API response means a task was accepted; the workflow waits for a terminal build/deploy status.
- Payload logging is for smoke testing only and should not be used in production.
- GitHub Actions deployment is intentionally gated by repository permissions and the configured secret; review changes before merging.
