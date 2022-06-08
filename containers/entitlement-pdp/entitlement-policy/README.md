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

# Rego policy language

## Rego reference

- https://www.openpolicyagent.org/docs/latest/policy-reference/
 
## Rego browser playground

- https://play.openpolicyagent.org/

## Rego quickref
There are a few key things to understand with Rego that tend to trip up people used to imperative languages (e.g. most of us)

1. It is not Turing-complete, it is guaranteed deterministic (Turning-complete languages are *not* guaranteed deterministic) - a Rego policy always resolves to either success or failure.
1. It in not imperative - it is rules-based. There is no guarantee about execution order of rules.
1. All rules must be valid for all data at all times - if undefined results are possible policy will not build. Think of every rule as a "for all possible (data/inputs)".
1. Rules are composable.
1. Rego rules operate exclusively on JSON data input documents (rooted under the `input.` namespace) to generate a single result.
1. Rego includes some helper functions to make network calls, parse JWTs, handle JSON and YAML, etc etc
1. Rego policies can be unit tested


You can copy this into https://play.openpolicyagent.org/ to evaluate it if you wish

``` rego

package play

# KEY REGO THING
# When satisfying a rule, the engine is always asking "Given the data I'm checking, is there a world in which ALL my terms can be true at the same time?"

foo := ["bar", "baz", "buz", "bar"]

# It is possible for all the terms in this rule to be True at the same time
test_bar_is_zero {
  some i
  "bar" == foo[i] # "bar" is in foo, so this term can be true given data "foo" as defined above
  i == 3 # "bar" appears at the 3rd index, so this term can be true given data "foo" as defined above
}

# It is possible for all the terms in this rule to be True at the same time
test_bar_is_three {
  some i
  "bar" == foo[i] # "bar" is in foo, so this term can be true given data "foo" as defined above
  i == 0 # "bar" appears at the 0th index, so this term can be true given data "foo" as defined above
}

# It is NOT possible for all the terms in this rule to be True at the same time
test_bar_is_zero_and_three_at_once {
  some i
  "bar" == foo[i] # "bar" is in foo, so this term can be true given data "foo" as defined above
  i == 3 # "bar" appears at the 3rd index, so this term can be true given data "foo" as defined above
  i == 0 # "bar" ALSO appears in the 0th index, but a given instance of "bar" in "foo" cannot be in both the 0th and 3rd index *at the same time*,
}

# so all 3 of these Rule terms can't all be True at the same time -> the rule is False

# It is possible for all the terms in this rule to be True at the same time
test_bar_is_zero_and_three {
  some i, j
  "bar" == foo[i] # "bar" is in foo, so this term can be true given data "foo" as defined above
  "bar" == foo[j] # "bar" is in foo, so this term can be true given data "foo" as defined above
  j == 3 # "bar" appears at the 3rd index, so this term can be true given data "foo" as defined above
  i == 0 # "bar" appears at the 0th index, so this term can be true given data "foo" as defined above
}

# This rule states 4 terms *that can all be true at the same time* thus this rule is True
# 1. "bar" exists at index i
# 2. "bar" exists at index j
# 3. "bar" index j can be 3
# 3. "bar" index i can be 0

# A simpler way to express `test_bar_is_zero_and_three` in one line without hardcoded indexes
# "Is it possible for bar to exist twice in the list?"
# "That is, is it true that there are 2 possible indexes that map to value "bar", and is it also true that for a case where this is true, that they are not the same index?""
test_bar_is_zero_and_three {
  some i, j
  foo[i] == "bar"
  foo[j] == "bar"
  i != j
}
```
