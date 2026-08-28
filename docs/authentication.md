# CPI authentication and endpoint run guide

## Authentication

The client reads `clientid`, `clientsecret`, `tokenurl`, and `url` from the local service-key JSON and uses OAuth 2.0 Client Credentials. The secret is never printed or included in flow payloads.

For package and design-time artifact operations, use a Process Integration Runtime `api` service key with the required content and deployment roles. The `integration-flow` plan is for calling deployed flow endpoints and is not sufficient for OData content management.

## Validate access

```powershell
cpi.exe --key-file .\CPI-API-KEY.json login
cpi.exe --key-file .\CPI-API-KEY.json list-packages
cpi.exe --key-file .\CPI-API-KEY.json list-artifacts
```

`login` validates OAuth only. `list-packages` and `list-artifacts` validate access to the Cloud Integration OData API.

## Troubleshooting

Do not save or print access tokens or client secrets. For `401`, check credentials. For `403`, check service-instance roles. For `404`, verify the API-client service URL and requested package or artifact ID.
