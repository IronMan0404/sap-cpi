# SAP_TIMER_GROOVY_DEMO

This is a new sample iFlow deployed into the existing `poc` package. Its complete
SAP artifact source is checked in under this directory.

## Processing design

`Start Timer 1` → `Content Modifier 1` → `Groovy Script 1` → `End`

- The timer starts the flow on the schedule stored in the exported SAP iFlow XML.
- The Content Modifier creates the `Hello World!` body.
- The Groovy script extracts the text, stores it in `extractedText`, and returns it as the body.
- The flow ends successfully; monitor it in Message Monitoring.

The `.iflw` file is SAP Cloud Integration's proprietary graphical-model representation.
It must originate from a valid SAP iFlow export. The local build only packages this
source; it does not invent or render the graphical model.

## Source-to-deployment

The GitHub workflow runs these operations:

1. Package this directory into `build/SAP_TIMER_GROOVY_DEMO.zip`.
2. Upload the new artifact to package `poc`.
3. Save the active version.
4. Deploy the artifact.
5. Verify runtime status.

Run it from GitHub Actions with **Deploy SAP Timer Groovy demo** → **Run workflow**.
Use `upload` for the first deployment and `deploy-only` for a repeat deployment.

## Local equivalent

```powershell
python scripts/build_iflow.py flows/SAP_TIMER_GROOVY_DEMO build/SAP_TIMER_GROOVY_DEMO.zip
cpi --key-file CPI-API-KEY.json login
cpi --key-file CPI-API-KEY.json flow upload --manifest config/SAP_TIMER_GROOVY_DEMO.yaml --bundle build/SAP_TIMER_GROOVY_DEMO.zip --apply
cpi --key-file CPI-API-KEY.json flow version --manifest config/SAP_TIMER_GROOVY_DEMO.yaml --apply
cpi --key-file CPI-API-KEY.json flow deploy --manifest config/SAP_TIMER_GROOVY_DEMO.yaml --apply
cpi --key-file CPI-API-KEY.json flow status --id SAP_TIMER_GROOVY_DEMO
```
