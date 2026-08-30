# SAP CPI GitOps Technical Specification

## 1. Purpose and scope

This repository provides source control, validation, and controlled delivery for
SAP Cloud Integration (CPI) integration-flow artifacts. It manages exported CPI
flow bundles and deployment metadata; it does not replace the SAP graphical
integration-flow designer.

The specification covers local development, the Python `cpi` CLI, GitHub Actions,
authentication, package/artifact lifecycle, runtime verification, and security.

## 2. Repository source of truth

The canonical source for a flow is `flows/<FLOW_ID>/`. The corresponding
manifest is `config/<FLOW_ID>.yaml`. The SAP-exported `.iflw` model and resource
files are authoritative for the graphical design and runtime behavior.

Current canonical flow:

| Flow | Package | Source | Manifest |
| --- | --- | --- | --- |
| `SAP_TIMER_GROOVY_DEMO` | `poc` | `flows/SAP_TIMER_GROOVY_DEMO` | `config/SAP_TIMER_GROOVY_DEMO.yaml` |

The Timer/Groovy flow contains a Timer Start Event, Content Modifier, Groovy
script, and end path. Its deployed CPI version is tracked in the manifest and
SAP bundle manifest. CPI-generated timestamps, download metadata, and line
ending changes are not design changes.

Required conventions:

- Use SAP artifact IDs and symbolic names exactly.
- Use uppercase SAP-style names for flow directories and deployment files.
- Keep one canonical source directory per artifact ID.
- Keep generated build output in ignored `build/`.
- Do not commit credentials or tenant-specific secret material.

## 3. Manifest contract

Each delivery manifest contains:

```yaml
package:
  id: poc
  name: POC
  version: 1.0.0

flow:
  id: SAP_TIMER_GROOVY_DEMO
  name: SAP Timer Groovy Demo
  version: 1.0.2
  template: ../build/SAP_TIMER_GROOVY_DEMO.zip
  configuration: {}

deployment:
  poll_seconds: 5
  timeout_seconds: 300
  max_attempts: 2
```

`package.id`, `flow.id`, `flow.name`, `flow.version`, and `flow.template` are
required. Deployment polling values must be positive; `max_attempts` must be at
least one. Package description, vendor, keywords, country, industry, and line
of business fields are optional metadata applied by `package update`.

The package manifest targets the existing editable package `poc`. Package
creation requires a separately exported package ZIP and is not part of the
normal existing-package flow release.

## 4. CLI interface and lifecycle

The CLI authenticates using an API-client service-key JSON file and exposes:

| Command | Responsibility |
| --- | --- |
| `login` | Validate OAuth client-credentials authentication |
| `flow pull` | Download an SAP artifact for review/migration |
| `flow build` | Package a checked-in SAP export into a ZIP |
| `flow upload` | Create a new artifact ID in a package |
| `flow update` | Replace the active draft of an existing artifact |
| `flow verify` | Compare a CPI-downloaded bundle with the local bundle using normalized digest rules |
| `flow version` | Save a semantic CPI version |
| `flow deploy` | Deploy a saved version and wait for terminal status/runtime start |
| `flow status` | Read deployed runtime status or deployment task status |
| `list messages` | Read message-processing logs |
| `package update` | Apply package overview metadata |

Existing-artifact release sequence:

```text
validate → build → flow update → verify active draft → save version
→ verify saved version → approval → deploy → runtime STARTED → monitor logs
```

New-artifact release replaces `flow update` with `flow upload`. A
`deploy-only` run skips source mutation and redeploys an already saved version.

Bundle verification ignores CPI-managed metadata (`metainfo.prop`, parameter
metadata, generated bundle version/origin fields, and text line-ending changes)
but detects changes to flow design, scripts, and meaningful resources.

## 5. GitHub Actions SDLC

The reusable workflow is `.github/workflows/sap-cpi-sdlc.yml`; flow-specific
workflows supply the manifest, source directory, bundle name, artifact ID,
operation, and release version.

Stages are:

```text
Validate → Build → Upload/Update → Verify Upload → Save Version
→ Verify Version → Protected Approval → Deploy → Verify Runtime → Monitor
```

The `cpi-production` GitHub Environment gates deployment. Runs targeting the
same artifact ID are serialized with GitHub concurrency to reduce CPI editor
lock conflicts. Deployment uses bounded retries from `deployment.max_attempts`
and remains failed if CPI reports a terminal failure after those attempts.

The workflow writes `CPI_SERVICE_KEY_JSON` to a temporary runner file, uses it,
and removes it during cleanup. It must never print or commit that file.

## 6. Authentication and trust boundaries

| Boundary | Credential | Responsibility |
| --- | --- | --- |
| Cloud Foundry | Human `cf login` | Inspect org, space, and service instances |
| CPI design-time API | Process Integration Runtime `api` service key | Read, upload, update, version, deploy, and monitor content |
| GitHub | User session/PAT | Commit, push, pull requests, and workflow administration |
| Deployment approval | Protected Environment reviewers | Authorize tenant mutation after verification |

The `integration-flow` plan is for invoking deployed flow endpoints and is not
the design-time content-management credential. The API URL is derived from the
API-client service key and normally ends at `/api/v1`.

## 7. Failure handling and limitations

- SAP iFlow graphical shapes cannot be reliably generated from YAML or JSON in
  this repository; valid SAP exports are required.
- CPI editor locks can reject updates. The user must release the lock before a
  new update attempt.
- Upload, update, version, and deploy are separate operations. Visibility in
  the CPI design UI does not prove runtime deployment.
- Deployment is asynchronous. The task must reach a successful terminal state,
  and the runtime artifact must report `STARTED`.
- Runtime parameters, credentials, certificates, keystores, destinations, and
  other tenant security material are managed outside the flow ZIP.
- CPI custom package tags require tenant-defined tag configuration and are not
  invented by this repository.
- Rollback means redeploying a previously verified saved version; automatic
  deletion or undeployment is not supported.
- Payload attachments/logging are acceptable for controlled smoke tests only,
  not for production workloads.

## 8. Security requirements

- Ignore and never commit `CPI-API-KEY.json`, `DEMO-API-KEY.json`, `.env`,
  tokens, private keys, or secrets.
- Do not include secrets in command output, test fixtures, documentation, or
  workflow logs.
- Use separate API-client credentials per tenant/environment.
- Require protected-environment approval for shared or production tenants.
- Review flow XML, Groovy, manifest, and workflow changes through pull requests.

## 9. Acceptance criteria

A repository change is acceptable when:

1. The canonical source and manifest identify the same SAP flow ID and name.
2. The bundle builds from `flows/<FLOW_ID>` without requiring a package ZIP.
3. All tests pass and all manifests/workflows parse successfully.
4. Existing artifacts use update; new IDs use upload.
5. Upload/version verification completes before deployment.
6. Deployment failure, timeout, lock, authentication, and runtime-not-started
   conditions fail with actionable diagnostics.
7. No sensitive file is tracked.
8. Documentation identifies SAP UI/Git integration boundaries and local CLI
   limitations.

## 10. References

- [SAP Integrating with GitHub](https://help.sap.com/docs/integration-suite/isuite-integrations-and-apis/integrating-with-github)
- [SAP Git Pull](https://help.sap.com/docs/integration-suite/isuite-integrations-and-apis/git-pull-gp)
- [SAP Integration Flow Example Requests](https://help.sap.com/docs/cloud-integration/sap-cloud-integration/integration-flow-example-requests)
- [SAP Integration Content API](https://help.sap.com/docs/cloud-integration/sap-cloud-integration/integration-content)
- [SAP Runtime Status API](https://help.sap.com/docs/cloud-integration/sap-cloud-integration/get-runtime-status-of-deployed-integration-flow)
