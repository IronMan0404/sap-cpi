# Smoke-test artifacts

Place the exported SAP Cloud Integration integration-flow artifact archive here as:

```text
SAP_SMOKE_TEST_FLOW.zip
```

For package creation, also provide the exported package archive as:

```text
SAP_SMOKE_TEST_PACKAGE.zip
```

The flow archive must contain the valid CPI iFlow bundle created from the SAP smoke-test scenario:

```text
Timer Start -> Content Modifier (Hello World!) -> Groovy Script (log payload)
```

The currently checked-in `SAP_SMOKE_TEST_FLOW.zip` is a basic `test1` HTTPS flow and is not a valid implementation of this smoke-test scenario. Replace it with an artifact exported from CPI after creating the three steps above. SAP validates the internal iFlow bundle structure during upload; the CLI does not generate that proprietary structure.

The package archive is optional when reusing an existing editable package such as `poc`. It is required only when creating a new package through `package create`.
