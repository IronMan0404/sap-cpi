# SAP CPI GitOps roadmap

## Goal

Manage SAP Cloud Integration content from Git while keeping SAP’s supported iFlow design and tenant controls intact.

## Current state

The repository currently provides:

- `sap-cpi` / `cpi` CLI with OAuth client-credentials authentication.
- Package listing, package creation, package download, and content inventory.
- Flow pull/download, upload, update, version, deploy, runtime status, and message monitoring.
- A manifest for existing package `poc` and flow `SAP_SMOKE_TEST_FLOW`.
- A GitHub Actions deployment workflow with `update`, `upload`, and `deploy-only` modes.
- Tests and documentation for the four smoke-test execution scenarios.

The repository does not generate SAP iFlow designs from YAML or JSON. The SAP-exported integration project/archive is the source of the actual flow model.

## Phase 1: establish the source of truth

1. Create or model `SAP_SMOKE_TEST_FLOW` in SAP Cloud Integration Design.
2. Use the required smoke-test design:

   ```text
   Timer Start → Content Modifier (Hello World!) → Groovy Script
   ```

3. Export the flow and place it at `artifacts/SAP_SMOKE_TEST_FLOW.zip`.
4. Commit the archive and its manifest in a pull request.
5. Ensure the CPI editor lock is released before CI updates the artifact.

Alternative: configure SAP’s native GitHub integration and import/clone the flow from the repository. SAP supports Git import, pull, and push for artifacts that are connected to a Git repository.

## Phase 2: local developer workflow

```text
flow pull → review/edit Git source → flow build → flow update/upload
→ flow version → flow deploy → flow status → list messages
```

Use `flow update` for an existing artifact and `flow upload` for a new artifact ID. Use `deploy-only` when the active version should be redeployed without modifying the draft.

## Phase 3: pull request validation

Add required checks before merge:

- Python tests.
- YAML manifest parsing.
- Artifact ZIP existence and readability.
- Artifact naming and flow ID checks.
- Secret scanning.
- Review of Groovy/resource changes.

Validation must not call mutating CPI APIs.

## Phase 4: GitHub Actions deployment

The current workflow deploys on demand and on content changes. It uses `CPI_SERVICE_KEY_JSON` from GitHub Actions Secrets and defaults to updating the existing artifact.

Recommended branch policy:

```text
feature branch → pull request → validation → protected main/master → deployment
```

Keep deployment credentials in GitHub Secrets. Do not store service keys, `.env` files, access tokens, certificates, or private keys in Git.

## Phase 5: promotion between tenants

For DEV/TEST/PROD landscapes, choose one controlled promotion mechanism:

- SAP Continuous Integration and Delivery job for SAP Integration Suite artifacts.
- SAP Cloud Transport Management / Content Agent Service.
- A reviewed GitHub Actions workflow calling the Integration Content API for each target tenant.

Do not use multiple systems as independent writers to the same artifact. Define one promotion owner and release process.

Remember that flow archives do not automatically provide tenant security material, keystores, credentials, destinations, or externalized runtime configuration. Those must be provisioned separately in each target tenant.

## Phase 6: production hardening

- Use separate API-client service keys per tenant and environment.
- Restrict GitHub environments and require approvals for TEST/PROD.
- Pin action versions and review dependency updates.
- Record deployment task IDs, artifact versions, commit SHAs, and target tenants.
- Add rollback by redeploying a known-good exported version.
- Add deployment locks/concurrency so two workflow runs cannot update the same artifact at once.
- Do not use payload logging in production.

## Supported versus unsupported responsibilities

| Responsibility | Repository/CLI | SAP CPI/GitHub/SAP CI&D |
| --- | --- | --- |
| Store and review source | Yes | Yes |
| Define deployment metadata | Yes, YAML | Yes |
| Model graphical iFlow shapes | No | CPI Web UI / SAP Git integration |
| Pull/export valid iFlow archive | Yes, API download | CPI/Git integration |
| Update existing artifact | Yes, API PUT | CPI API |
| Save version and deploy | Yes, API | CPI API / CI&D |
| Configure credentials and keystores | No | Tenant administration |
| Promote content across tenants | Partially | SAP CI&D / Transport Management recommended |

## Official SAP references

- [Integrating with GitHub](https://help.sap.com/docs/integration-suite/isuite-integrations-and-apis/integrating-with-github)
- [Git Pull](https://help.sap.com/docs/integration-suite/isuite-integrations-and-apis/git-pull-gp)
- [Integration Flow Example Requests](https://help.sap.com/docs/cloud-integration/sap-cloud-integration/integration-flow-example-requests)
- [Integration Content](https://help.sap.com/docs/cloud-integration/sap-cloud-integration/integration-content)
- [Configure SAP Integration Suite Artifacts Job](https://help.sap.com/docs/continuous-integration-and-delivery/sap-continuous-integration-and-delivery/configure-sap-integration-suite-artifacts-job-in-job-editor)
- [Setting Up Content Transport](https://help.sap.com/docs/cloud-integration/sap-cloud-integration/f4bf46bd9dbe4d08b7ee3c66b55b15a3.html)
