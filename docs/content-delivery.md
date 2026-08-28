# CPI content delivery

## CLI-only trial setup

Target the Cloud Foundry trial space:

```powershell
cf login -a https://api.cf.us10-001.hana.ondemand.com
cf target -o 0b9eab52trial -s dev
cf target
```

Create the API-plan service instance and service key using the repository role configuration:

```powershell
cf create-service it-rt api CPI-API-CLI -c .\config\api-service-params.json --wait

cf create-service-key CPI-API-CLI CPI-API-CLI-KEY
cf service CPI-API-CLI
cf service-keys CPI-API-CLI
cf service-key CPI-API-CLI CPI-API-CLI-KEY
```

Save only the JSON object returned by the final command as `CPI-API-KEY.json`. The output contains a client secret: never paste it into chat, commit it, or add it to documentation. The repository `.gitignore` excludes local service-key files.

Validate the new API credentials and OData access:

```powershell
cpi.exe --key-file .\CPI-API-KEY.json login
cpi.exe --key-file .\CPI-API-KEY.json list-packages
cpi.exe --key-file .\CPI-API-KEY.json list-artifacts

# Optional: download an existing package as a local ZIP template
cpi.exe --key-file .\CPI-API-KEY.json package download --id poc --output .\artifacts\poc-package.zip
```

### Reuse an existing package or create a new one

For an editable existing package, set `package.id: poc` in the manifest and run `flow upload` directly. A package template is not required for flow upload. Use a unique `flow.id`, or use the existing artifact ID only when intentionally updating it.

To create a new package such as `SAP_SMOKE_TEST`, use a separate manifest (or add the package `template` field temporarily) with a real exported package ZIP such as `artifacts/SAP_SMOKE_TEST_PACKAGE.zip`. A flow artifact ZIP cannot be used as a package ZIP. Run `package create --apply` before uploading the flow.

The existing `DEMO-API-KEY.json` belongs to the `integration-flow` plan and is for deployed flow calls, not package or design-time artifact management.

For `cmd.exe`, use one-line commands. PowerShell uses the backtick character for continuation, but `cmd.exe` does not:

```cmd
cpi.exe --key-file .\CPI-API-KEY.json flow upload --manifest .\config\SAP_SMOKE_TEST.yaml --bundle .\build\SAP_SMOKE_TEST_FLOW.zip --apply
```

The delivery CLI uses a YAML manifest and a CPI artifact ZIP template. Credentials stay in a service key; the manifest contains no secrets.

Create a **Process Integration Runtime** service instance with the `api` plan and the roles required to create, update, version, and deploy content. The existing `integration-flow` key is for calling deployed flows and is not sufficient for these OData operations.

Start with [config/cpi.example.yaml](../config/cpi.example.yaml), then place the package and flow templates under the paths specified in the manifest. Configuration values are substituted for `{{name}}` and `{{ name }}` in UTF-8 template files.

Build and inspect the flow locally:

```powershell
cpi.exe flow build --manifest .\config\cpi.example.yaml --output .\build\MY_FLOW.zip
```

All mutating commands are dry-run unless `--apply` is supplied:

```powershell
cpi.exe --key-file .\CPI-API-KEY.json package create --manifest .\config\cpi.example.yaml
cpi.exe --key-file .\CPI-API-KEY.json flow upload --manifest .\config\cpi.example.yaml
cpi.exe --key-file .\CPI-API-KEY.json flow version --manifest .\config\cpi.example.yaml
cpi.exe --key-file .\CPI-API-KEY.json flow deploy --manifest .\config\cpi.example.yaml
```

Apply changes explicitly:

```powershell
cpi.exe --key-file .\CPI-API-KEY.json package create --manifest .\config\cpi.example.yaml --apply
cpi.exe --key-file .\CPI-API-KEY.json flow upload --manifest .\config\cpi.example.yaml --bundle .\build\MY_FLOW.zip --apply
cpi.exe --key-file .\CPI-API-KEY.json flow version --manifest .\config\cpi.example.yaml --apply
cpi.exe --key-file .\CPI-API-KEY.json flow deploy --manifest .\config\cpi.example.yaml --apply
cpi.exe --key-file .\CPI-API-KEY.json flow status --id MY_FLOW
```

Deployment waits for the SAP build/deploy task to reach a terminal state, then reads runtime status. A failed deployment is returned as an error result; the CLI does not automatically overwrite or undeploy an existing artifact. Mutating API calls fetch CSRF tokens from the tenant `/$metadata` endpoint and reuse the authenticated session.

During flow creation, CPI assigns the draft version automatically. The CLI therefore does not send `Version` in the initial upload request. The version command must run only after the upload succeeds. Package creation is required for a new package, but is skipped when uploading into an existing package.
