# Cloud Foundry and SAP CPI setup

## Install and log in

Install Cloud Foundry CLI v8 using the [SAP tutorial](https://developers.sap.com/tutorials/cp-cf-download-cli..html). Open a new PowerShell window after installation:

```powershell
cf version
cf login -a https://api.cf.us10-001.hana.ondemand.com
```

Select organization `0b9eab52trial` and space `dev`.

Verify the target:

```powershell
cf target
```

Expected values:

```text
API endpoint: https://api.cf.us10-001.hana.ondemand.com
org:         0b9eab52trial
space:       dev
```

## Check the CPI instance

```powershell
cf services
cf service PIR-DEV
cf service-keys PIR-DEV
```

Expected service:

```text
Name:  PIR-DEV
Plan:  integration-flow
Space: dev
```

The local `DEMO-API-KEY.json` and `.env` files contain OAuth configuration and are ignored by Git.

## Install and run the project CLI

From `C:\work\SAP-CPI`:

```powershell
py -m pip install -e ".[dev]"
sap-cpi --help
cpi.exe --help
```

Commands migrated from the old CPI CLI concept:

```powershell
cpi.exe login
cpi.exe list content
cpi.exe list messages --errors --top 10
cpi.exe download --id <IFLOW_ID> --output .\downloads\<IFLOW_ID>.zip
```

PowerShell reserves `cpi` as an alias for `Copy-Item`; use `cpi.exe`.

## Credential safety

Never share the output of:

```powershell
cf service-key PIR-DEV DEMO-API-KEY
```

If the client secret is exposed, recreate the service key in SAP BTP and update `.env`.
