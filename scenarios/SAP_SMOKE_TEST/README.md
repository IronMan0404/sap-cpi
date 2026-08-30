# SAP_SMOKE_TEST

## Purpose

This scenario verifies SAP Cloud Integration by running one timer-triggered integration flow without sender or receiver systems.

The deployed flow is:

```text
Timer Start Event
    -> Content Modifier: Hello World!
    -> Groovy Script: write payload to the message-processing log
```

The flow design is documented in [SAP_SMOKE_TEST_FLOW/README.md](../../SAP_SMOKE_TEST_FLOW/README.md).

## Scenario 1: build the flow artifact

What: validate the exported SAP iFlow template and create the named build artifact.

How:

```powershell
cpi.exe flow build --manifest .\config\SAP_SMOKE_TEST.yaml --output .\build\SAP_SMOKE_TEST_FLOW.zip
```

Expected result: `build/SAP_SMOKE_TEST_FLOW.zip` is created. The ZIP must be exported from CPI and contain the three required steps; the CLI does not create SAP’s proprietary iFlow format.

To pull the current active artifact from CPI before reviewing or building locally:

```powershell
cpi.exe --key-file .\CPI-API-KEY.json flow pull --manifest .\config\SAP_SMOKE_TEST.yaml --version active
```

## Scenario 2: select or create the package

### Reuse existing package

The active manifest targets the existing editable package `poc`. Skip package creation.

```powershell
cpi.exe --key-file .\CPI-API-KEY.json list-packages
```

### Create new package

Use a separate manifest with package ID `SAP_SMOKE_TEST` and a real package archive named `artifacts/SAP_SMOKE_TEST_PACKAGE.zip`:

```powershell
cpi.exe --key-file .\CPI-API-KEY.json package create --manifest .\config\SAP_SMOKE_TEST_CREATE_PACKAGE.yaml --apply
```

Expected result: the selected package exists in the tenant before flow upload.

## Scenario 3: upload, version, and deploy

What: place `SAP_SMOKE_TEST_FLOW` in the selected package, save version `1.0.0`, and deploy it.

How:

```powershell
cpi.exe --key-file .\CPI-API-KEY.json flow upload --manifest .\config\SAP_SMOKE_TEST.yaml --bundle .\build\SAP_SMOKE_TEST_FLOW.zip --apply
cpi.exe --key-file .\CPI-API-KEY.json flow version --manifest .\config\SAP_SMOKE_TEST.yaml --apply
cpi.exe --key-file .\CPI-API-KEY.json flow deploy --manifest .\config\SAP_SMOKE_TEST.yaml --apply
```

Expected result: CPI returns a deployment task that reaches a successful terminal status.

## Scenario 4: monitor message processing

What: verify that the timer ran the flow and that the payload was logged.

How:

```powershell
cpi.exe --key-file .\CPI-API-KEY.json flow status --id SAP_SMOKE_TEST_FLOW
cpi.exe --key-file .\CPI-API-KEY.json list messages --top 20
cpi.exe --key-file .\CPI-API-KEY.json list messages --errors --top 20
```

Expected result: the runtime artifact is active, a successful message exists for `SAP_SMOKE_TEST_FLOW`, and the message log contains `Hello World!`.
