# Example entitlement Rego policy

## Setup (Mac)

- `brew install opa`
- (Optional) `brew install opcr-io/tap/policy` (for packaging and publishing policy as OCI bundle)
- (Optional) VSCode
- (Optional) VSCode OPA plugin: https://marketplace.visualstudio.com/items?itemName=tsandall.opa
- (Optional) VSCode Rego linter https://marketplace.visualstudio.com/items?itemName=Plex.vscode-regolint

## Test (CI)

`make test`

## Test/debug (Interactive)

- Open folder in VSCode with above plugins and OPA installed
- Run `OPA: Execute Package` command to evaluate all files
- Run `OPA: Evaluate Selection` to evaluate a highlighted selection
  - Note that if you try to evaluate a section that uses variables declared outside the selection, you will get errors about "unsafe variables", since OPA can't see where you defined them if you pass it an incomplete snippet.
- Run `OPA: Test Workspace` command to run all `_test.rego` files
  - Tests are just regular rules with a unique filename, so you can evaluate them individually just like you evaluate rules in the above section
  
## Package policy bundle

``` sh
make policybuild
```

## Publish policy bundle

``` sh
make policypush
```
