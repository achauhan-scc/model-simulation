# Agent Under Test: Governed

## Purpose

Define the governed profile applied by the shared `azd` and Bicep project under `agent-under-test`.

This directory does not contain a second agent implementation or an independent infrastructure stack. It contains governed configuration, policies, and expected control outcomes.

- Prompt Agent instruction version.
- Tool API version.
- Scenario version.
- Simulator fixture version.
- Synthetic dataset version.

Only governance-relevant infrastructure, identity, policies, and runtime configuration should differ from the baseline.

Planned protections include:

- Applicable content-safety and RAI controls.
- Authenticated ingress and network isolation.
- Egress destination enforcement.
- Request, token, step, duration, and tool-call budgets.
- Explicit tool allowlisting.
- Least-privilege agent identity.
- Parameter-level action authorization.
- Human approval for high-value actions.
- Correlated telemetry, detection, and an operator stop.

## Planned structure

```text
agent-under-test-governed\
  config\
  policies\
  expected-controls\
  README.md
```

The shared deployment selects these protections through the `governed` `azd` environment and Bicep governance-profile parameter. No governed configuration, policy, or expected-control artifacts have been added yet.
