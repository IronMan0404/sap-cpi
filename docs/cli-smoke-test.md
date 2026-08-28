# Four CLI-only smoke-test scenarios

These scenarios automate the SAP [Smoke Test Scenario](https://help.sap.com/docs/cloud-integration/sap-cloud-integration/smoke-test-scenario). The target integration flow is:

```text
Timer Start Event -> Content Modifier (message body: Hello World!) -> Groovy Script (log payload)
```

There is no sender or receiver system. Deployment triggers the timer, the Content Modifier creates the message, and the Script step writes the payload to the message-processing log. SAP cautions that payload logging is for smoke testing only and is not a productive design pattern.

Important: the current local `artifacts/SAP_SMOKE_TEST_FLOW.zip` and `build/SAP_SMOKE_TEST_FLOW.zip` are simple `test1` bundles with an HTTPS start/end flow. They are not the SAP smoke-test flow described above. Replace the flow ZIP with an export containing the three required steps before treating the deployment as a smoke-test result.

## Smoke-test flow map

Each scenario below documents what the operation does, how to run it, and the expected result:

| Scenario | What it does | Main command | Success means |
| --- | --- | --- | --- |
| 1. Build locally | Validates the flow template and creates the artifact ZIP | `flow build` | A flow ZIP is created under `build/` |
| 2. Select a package | Reuses editable package `poc`, or creates a new package from a package ZIP | `package create` only for a new package | The target package exists and is editable |
| 3. Upload and deploy | Uploads the flow, saves version `1.0.0`, and deploys it | `flow upload`, `flow version`, `flow deploy` | CPI returns a deployment task that completes successfully |
| 4. Verify runtime | Checks runtime state and message-processing logs | `flow status`, `list messages` | The flow is active and a successful `Hello World!` message is logged |

The current `config/SAP_SMOKE_TEST.yaml` is configured for Scenario 2A and uses the existing package `poc`. It does not create a package.

The commands below are written for `cmd.exe` and are intentionally single-line commands. Do not paste PowerShell backticks into `cmd.exe`; `cmd.exe` treats the continuation lines as separate commands.

## One-time setup

Use a valid exported SAP smoke-test **package ZIP** and flow **artifact ZIP**. The CLI does not invent SAP’s proprietary iFlow bundle format. Copy them into the paths in `config/cpi.example.yaml`, or create a dedicated manifest such as `config/SAP_SMOKE_TEST.yaml`.

Use a Process Integration Runtime `api` service key with package/artifact write and deployment roles:

```powershell
cf login -a https://api.cf.us10-001.hana.ondemand.com
cf target -o 0b9eab52trial -s dev
cf create-service it-rt api CPI-API-CLI -c .\config\api-service-params.json --wait
cf create-service-key CPI-API-CLI CPI-API-CLI-KEY
cf service-key CPI-API-CLI CPI-API-CLI-KEY
cpi.exe --key-file .\CPI-API-KEY.json login
```

The `cf service-key` output contains a client secret. Save only the JSON object into `CPI-API-KEY.json`; never paste it into source control or chat. If the instance or key already exists, skip the corresponding create command.

## Scenario 1: validate and build locally

Purpose: confirm the exported SAP flow template, substitutions, and ZIP output without contacting CPI.

Before running this command in a new project, create the flow in CPI with the following exact steps:

1. Add a Timer Start Event and configure the scheduler as `Run Once` for a smoke test.
2. Add a Content Modifier after the Timer and set the message body to `Hello World!`.
3. Add a Groovy Script step after the Content Modifier that logs the payload to the message-processing log.
4. Connect the steps in that order, save the flow, and export/download its artifact ZIP into `artifacts/SAP_SMOKE_TEST_FLOW.zip`.

The CLI can upload and deploy an exported CPI artifact, but it cannot construct SAP’s proprietary iFlow ZIP format from YAML.

```powershell
cpi.exe flow build --manifest .\config\SAP_SMOKE_TEST.yaml --output .\build\SAP_SMOKE_TEST_FLOW.zip
cpi.exe package create --manifest .\config\SAP_SMOKE_TEST.yaml
cpi.exe flow upload --manifest .\config\SAP_SMOKE_TEST.yaml --bundle .\build\SAP_SMOKE_TEST_FLOW.zip
cpi.exe flow deploy --manifest .\config\SAP_SMOKE_TEST.yaml
```

Expected result: `flow build` reports `status: built`; mutating commands report `dryRun: true` and make no tenant changes.

## Scenario 2A: reuse the existing package

The tenant currently has an editable package named `poc` (version `1.0.0`) containing artifact `test1`. To reuse it, change the manifest package ID to `poc`:

```yaml
package:
  id: poc
```

Skip `package create` and continue with Scenario 3. A package template is not required for `flow upload`. Keep a unique flow ID unless you intentionally want to update `test1`.

## Scenario 2B: create the package

Purpose: import the smoke-test package into the tenant’s Design area.

For this path, use a separate manifest (or temporarily change `config\\SAP_SMOKE_TEST.yaml`) with a new package ID and a real package template:

```yaml
package:
  id: SAP_SMOKE_TEST
  name: SAP Smoke Test
  version: 1.0.0
  template: ../artifacts/SAP_SMOKE_TEST_PACKAGE.zip
```

```powershell
cpi.exe --key-file .\CPI-API-KEY.json package create --manifest .\config\SAP_SMOKE_TEST.yaml --apply
cpi.exe --key-file .\CPI-API-KEY.json list-packages
```

Expected result: package creation succeeds and the package ID from the manifest appears in the package list. Use this path only when creating a new package.

If the command reports `Package template not found`, the file `artifacts\SAP_SMOKE_TEST_PACKAGE.zip` is absent. A flow ZIP is not a package ZIP. Either obtain/export the package ZIP or use Scenario 2A with the existing `poc` package. If package creation fails, do not continue to flow version or deployment.

## Scenario 3: upload, version, and deploy the flow

Purpose: create the flow artifact, save version `1.0.0`, deploy it, and wait for SAP’s build/deploy task.

```powershell
cpi.exe flow build --manifest .\config\SAP_SMOKE_TEST.yaml --output .\build\SAP_SMOKE_TEST_FLOW.zip

cpi.exe --key-file .\CPI-API-KEY.json flow upload --manifest .\config\SAP_SMOKE_TEST.yaml --bundle .\build\SAP_SMOKE_TEST_FLOW.zip --apply

cpi.exe --key-file .\CPI-API-KEY.json flow version --manifest .\config\SAP_SMOKE_TEST.yaml --apply

cpi.exe --key-file .\CPI-API-KEY.json flow deploy --manifest .\config\SAP_SMOKE_TEST.yaml --apply
```

Expected result: deployment returns a task ID, reaches a successful terminal state, and runtime status is returned. The timer starts the flow according to the SAP smoke-test configuration. If upload returns HTTP 400, inspect the CPI error detail; the CLI omits `Version` during initial creation because CPI auto-generates the draft version.

## Scenario 4: verify runtime processing and Hello World

Purpose: confirm the deployed flow processed successfully and produced the expected message-processing log.

```powershell
cpi.exe --key-file .\CPI-API-KEY.json flow status --id SAP_SMOKE_TEST_FLOW
cpi.exe --key-file .\CPI-API-KEY.json list messages --top 20
cpi.exe --key-file .\CPI-API-KEY.json list messages --errors --top 20
```

Expected result:

- Runtime status is started/active according to the tenant response.
- A message exists for `SAP_SMOKE_TEST_FLOW` with completed/success status.
- The error-only query returns no entry for this run.
- The message log contains `Hello World!`.

If the timer is configured as run-once, redeploy the flow to run it again. Do not use the smoke-test payload logging pattern in production because SAP warns that logging payloads can create memory and performance problems.

## API behavior

Package creation uses `POST /api/v1/IntegrationPackages`; flow management uses `IntegrationDesigntimeArtifacts`; deployment uses `DeployIntegrationDesigntimeArtifact`, `BuildAndDeployStatus`, and `IntegrationRuntimeArtifacts`. Mutating calls use CSRF-token fetching. See SAP’s [Integration Content API](https://help.sap.com/docs/cloud-integration/sap-cloud-integration/integration-content) and [deployment status API](https://help.sap.com/docs/cloud-integration/sap-cloud-integration/get-runtime-status-of-deployed-integration-flow).
