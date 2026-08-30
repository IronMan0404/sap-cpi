# SAP CPI POC

Python proof of concept for connecting to SAP Cloud Integration on SAP BTP, validating OAuth access, and inventorying integration content.

Architecture and trust boundaries: [docs/architecture.md](docs/architecture.md)

Shareable local setup guide: [docs/local-setup.md](docs/local-setup.md)

Normative repository contract: [docs/specs/SAP_CPI_GITOPS_SPEC.md](docs/specs/SAP_CPI_GITOPS_SPEC.md). The repo-local agent guidance is [.codex/skills/sap-cpi-gitops/SKILL.md](.codex/skills/sap-cpi-gitops/SKILL.md).

## Security

The local `DEMO-API-KEY.json` file is intentionally ignored by Git. Never commit, paste, or log its `clientsecret`. If the key is exposed, revoke and recreate it in SAP BTP.

## Setup

Requires Python 3.10+.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
```

### Cloud Foundry CLI

Install Cloud Foundry CLI v8 using the [SAP Cloud Foundry CLI tutorial](https://developers.sap.com/tutorials/cp-cf-download-cli..html), then log in:

```powershell
cf version
cf login -a https://api.cf.us10-001.hana.ondemand.com
```

Select organization `0b9eab52trial` and space `dev`, then verify:

```powershell
cf target
cf services
cf service PIR-DEV
cf service-keys PIR-DEV
```

Do not paste the output of `cf service-key PIR-DEV DEMO-API-KEY`; it contains client credentials.

The client defaults to `./DEMO-API-KEY.json`. To use another file:

```powershell
sap-cpi --key-file .\DEMO-API-KEY.json health
sap-cpi --key-file .\DEMO-API-KEY.json list-packages
sap-cpi --key-file .\DEMO-API-KEY.json list-artifacts
```

The migrated SAP-style commands are also installed as `cpi.exe` on Windows. PowerShell has a built-in `cpi` alias for `Copy-Item`, so use the `.exe` suffix:

```powershell
cpi.exe --help
cpi.exe login
cpi.exe status
cpi.exe list content
cpi.exe list messages --errors --top 10
cpi.exe download --id MY_FLOW --output .\downloads\MY_FLOW.zip
```

`cf` manages Cloud Foundry accounts and service instances. `cpi.exe` is this project’s modern OAuth/OData client; it is not the old 2019 alpha binary from the SAP Community blog.


## SAP prerequisite

The existing `PIR-DEV` instance uses the `integration-flow` plan. It is intended for authenticating calls to an integration-flow endpoint. For OData package/artifact inventory, create a separate inbound API-client service instance using the `api` plan and assign only the roles required for reading integration content. Put that service key in a separate local JSON file and pass it with `--key-file`.

The OData service root is `<service-key-url>/api/v1`. A successful `login` only validates OAuth; it does not prove that the credential can access OData resources. If `health` or `list content` returns HTTP 404, use the URL from the API-client service key and verify its Cloud Integration API roles. `CPI_API_PATH` is available for tenants that expose a different API path.

See [scenarios/SAP_SMOKE_TEST/README.md](scenarios/SAP_SMOKE_TEST/README.md) for the four scenario steps, [SAP_SMOKE_TEST_FLOW/README.md](SAP_SMOKE_TEST_FLOW/README.md) for the flow design, [docs/gitops.md](docs/gitops.md) for local/GitHub deployment, `docs/cloud-foundry-setup.md` for setup, `docs/content-delivery.md` for package/flow delivery, and `docs/authentication.md` for CPI authentication.

See [docs/ROADMAP.md](docs/ROADMAP.md) for the SAP-supported Git/GitHub integration roadmap, promotion options, and limitations.

For package and flow creation, upload, versioning, and deployment, see `docs/content-delivery.md` and `config/cpi.example.yaml`.

The CLI-only API credential setup is documented there as well, including `cf service-key CPI-API-CLI CPI-API-CLI-KEY`.

For Windows `cmd.exe`, use the documented one-line CLI commands. PowerShell backticks are not valid command continuations in `cmd.exe`.

## Deploy the smoke-test flow into the existing package

The current manifest uses the existing editable package `poc`. The flow itself must first be created in the SAP Cloud Integration Design workspace because SAP’s iFlow ZIP format is proprietary and cannot be generated from this Python project.

In package `poc`, create an Integration Flow with this ID and name:

```text
ID:   SAP_SMOKE_TEST_FLOW
Name: SAP Smoke Test Flow
```

Model these connected steps in the flow:

```text
Timer Start Event -> Content Modifier -> Groovy Script
```

Configure them as follows:

1. Timer Start Event: open Scheduler and choose `Run Once` for the smoke test.
2. Content Modifier: on Message Body, enter exactly `Hello World!`.
3. Groovy Script: log the message body to the message-processing log. Use SAP’s supported message-log API, for example:

```groovy
import com.sap.gateway.ip.core.customdev.util.Message

def Message processData(Message message) {
    def body = message.getBody(String)
    def messageLog = messageLogFactory.getMessageLog(message)
    if (messageLog != null) {
        messageLog.addAttachmentAsString('Payload', body, 'text/plain')
    }
    return message
}
```

Save the flow, export/download its artifact ZIP from CPI, and replace:

```text
artifacts/SAP_SMOKE_TEST_FLOW.zip
```

The previously deployed `SAP_SMOKE_TEST_FLOW` was based on a placeholder HTTPS flow. Delete that artifact from package `poc` in the CPI Design workspace before uploading the corrected flow with the same ID.

From the repository root, run:

```powershell
cpi.exe flow build --manifest .\config\SAP_SMOKE_TEST.yaml --output .\build\SAP_SMOKE_TEST_FLOW.zip
cpi.exe --key-file .\CPI-API-KEY.json flow upload --manifest .\config\SAP_SMOKE_TEST.yaml --bundle .\build\SAP_SMOKE_TEST_FLOW.zip --apply
cpi.exe --key-file .\CPI-API-KEY.json flow version --manifest .\config\SAP_SMOKE_TEST.yaml --apply
cpi.exe --key-file .\CPI-API-KEY.json flow deploy --manifest .\config\SAP_SMOKE_TEST.yaml --apply
cpi.exe --key-file .\CPI-API-KEY.json flow status --id SAP_SMOKE_TEST_FLOW
cpi.exe --key-file .\CPI-API-KEY.json list messages --top 20
```

Do not run `package create` for this path. It is only for creating a new package from `config/SAP_SMOKE_TEST_CREATE_PACKAGE.yaml` and `artifacts/SAP_SMOKE_TEST_PACKAGE.zip`. Payload logging is suitable only for this smoke test; do not use it in production.

GitHub Actions uses explicit SDLC stages: `Validate`, `Build`, `Upload/Update`,
`Verify Upload`, `Save Version`, `Verify Version`, approval in the protected
`cpi-production` Environment, `Deploy`, `Verify Runtime`, and `Monitor`. Start
a release from the flow workflow's **Run workflow** action and provide a new
semantic version such as `1.0.1`. The workflow builds the ZIP from
`<FLOW_ID>` and keeps the service key only in GitHub Actions Secrets.

Package metadata is defined in the flow manifest and can be applied to the
existing package with:

```powershell
cpi.exe --key-file .\CPI-API-KEY.json package update --manifest .\config\SAP_TIMER_GROOVY_DEMO.yaml --apply
```

Release the CPI package editor lock before running this command. Tenant custom
tags must be defined by a CPI administrator first.

## Development

```powershell
pytest
```
