# Local SAP CPI CLI Setup

This guide prepares a Windows developer machine to use this repository's `cpi.exe` CLI with an SAP Cloud Integration tenant.

## 1. Prerequisites

Install Git and Python 3.10 or later. Obtain an API-client service key from the target Process Integration Runtime `api` plan. The `integration-flow` plan is for calling deployed endpoints, not package and artifact management.

Check the tools:

```powershell
git --version
py --version
```

## 2. Clone the repository

```powershell
git clone https://github.com/IronMan0404/sap-cpi.git
cd sap-cpi
git switch -c feature/<your-name>
```

## 3. Install the local CLI

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Verify:

```powershell
cpi.exe --help
python -m pip show sap-cpi
```

PowerShell has a built-in `cpi` alias for `Copy-Item`; use `cpi.exe`.

## 4. Configure the CPI service key

Create a service instance in the target BTP subaccount:

```text
Service: Process Integration Runtime
Plan: api
Service key: CPI-API-KEY
```

Save the complete JSON service key in the repository root as:

```text
CPI-API-KEY.json
```

This filename is ignored by Git. Never commit, paste, email, or print it because it contains `clientsecret`.

## 5. Verify CPI access

```powershell
cpi.exe --key-file .\CPI-API-KEY.json login
cpi.exe --key-file .\CPI-API-KEY.json health
cpi.exe --key-file .\CPI-API-KEY.json list-packages
cpi.exe --key-file .\CPI-API-KEY.json list-artifacts
```

`login` validates OAuth. The remaining commands validate CPI OData access.

## 6. Optional Cloud Foundry check

Cloud Foundry identifies the BTP subaccount and service space; it is not the credential used by `cpi.exe`.

```powershell
cf logout
cf api https://api.cf.us10-001.hana.ondemand.com
cf login
cf orgs
cf target -o "<organization-name>"
cf spaces
cf target -s "<space-name>"
cf target
```

The organization, space, and CPI service key must belong to the same subaccount.

## 7. Build and test the demo

SAP graphical iFlow designs must originate from a valid SAP export. This repository packages the SAP project and does not generate graphical flow XML from YAML.

Root-level source projects:

```text
SAP_SMOKE_TEST_FLOW/
SAP_TIMER_GROOVY_DEMO/
```

Build and test:

```powershell
python scripts/build_iflow.py SAP_TIMER_GROOVY_DEMO build/SAP_TIMER_GROOVY_DEMO.zip
python -m pytest -q
```

## 8. Deploy an existing artifact

Use `flow update` when the artifact already exists in the CPI package:

```powershell
cpi.exe --key-file .\CPI-API-KEY.json flow update `
  --manifest .\config\SAP_TIMER_GROOVY_DEMO.yaml `
  --bundle .\build\SAP_TIMER_GROOVY_DEMO.zip `
  --version 1.0.4 --apply
```

Save and deploy the version:

```powershell
cpi.exe --key-file .\CPI-API-KEY.json flow version `
  --manifest .\config\SAP_TIMER_GROOVY_DEMO.yaml `
  --version 1.0.4 --apply

cpi.exe --key-file .\CPI-API-KEY.json flow deploy `
  --manifest .\config\SAP_TIMER_GROOVY_DEMO.yaml `
  --version 1.0.4 --apply
```

Check the result:

```powershell
cpi.exe --key-file .\CPI-API-KEY.json flow status --id SAP_TIMER_GROOVY_DEMO
cpi.exe --key-file .\CPI-API-KEY.json list messages --top 20
```

Use `flow upload` only for a new artifact ID. Release the CPI editor lock before updating.

## 9. Troubleshooting

| Error | Action |
| --- | --- |
| `cpi` runs Copy-Item | Use `cpi.exe` |
| Invalid JSON service key | Download the complete API-plan service key again |
| HTTP 404 | Check the API-client service-key URL and tenant |
| HTTP 403 | Check service-instance roles and access |
| Artifact locked | Release the flow lock in CPI Design |
| Artifact already exists | Use `flow update`, not `flow upload` |
| Deployment task failed | Inspect CPI deployment status and runtime logs |

## 10. Daily workflow

```text
git pull
edit the SAP-exported project/resources
python -m pytest -q
build the flow ZIP
git add / commit / push
open or update a pull request
run the approved GitHub Actions deployment
```

GitHub Actions uses the repository secret `CPI_SERVICE_KEY_JSON`. Do not commit the local service-key file.

