# Hackbot CI

This action is used to launch the Hackbot service and scan a contract for vurnabilities.

## Inputs

- `bot_address`: The address of the service.
- `bot_port`: The port of the service.

## Outputs

- `hack_results`: The results of the hack.

## Example

```yaml
name: Test Action Workflow

on:
  workflow_dispatch:

jobs:
  test-action:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Run Test Action
        uses: gatlingX/hackbot-ci@main
        with:
          bot_address: "localhost"
          bot_port: "5000"
        id: test-action

      - name: Print output
        run: |
          echo "Hack result: ${{ steps.test-action.outputs.hack_result }}"  
```
