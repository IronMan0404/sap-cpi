# SAP_SMOKE_TEST_FLOW

## Flow purpose

This is the only integration flow in the `SAP_SMOKE_TEST` scenario. It proves that the tenant can schedule, process, log, deploy, and monitor an SAP Cloud Integration message.

## Design

| Order | SAP shape | Required configuration | Runtime behavior |
| --- | --- | --- | --- |
| 1 | Timer Start Event | Scheduler: `Run Once` for the smoke test | Starts processing after deployment |
| 2 | Content Modifier | Message Body: `Hello World!` | Creates the message payload |
| 3 | Groovy Script | Log the message body/payload | Writes the payload to the message-processing log |

Connect the shapes in exactly this order. Do not add an HTTPS sender, receiver adapter, weather call, or external system to this scenario.

## Naming

| Item | Name |
| --- | --- |
| Package ID | `poc` when reusing the existing package; `SAP_SMOKE_TEST` for a new package |
| Flow ID | `SAP_SMOKE_TEST_FLOW` |
| Flow artifact | `artifacts/SAP_SMOKE_TEST_FLOW.zip` |
| Build artifact | `build/SAP_SMOKE_TEST_FLOW.zip` |
| Manifest | `config/SAP_SMOKE_TEST.yaml` |

## Artifact requirement

The artifact ZIP must be exported/downloaded from SAP Cloud Integration after creating the flow in the Design workspace. The local placeholder previously contained `test1` with an HTTPS start/end flow and must not be used as proof of this scenario.

## Deployment sequence

Run the commands in [scenario documentation](../../scenarios/SAP_SMOKE_TEST/README.md), in order: build, select/create package, upload, version, deploy, and monitor.
