# Agent Under Test: Baseline

## Purpose

Represent the developer-built customer-support Prompt Agent that relies heavily on model instructions and lacks independent governance protections.

This directory is the single Azure Developer CLI project used to deploy both demo environments. It will own:

- The shared Prompt Agent instructions and tool configuration.
- Tool definitions.
- Synthetic refund and customer-record workflow.
- Synthetic data.
- Parameterized Bicep infrastructure.
- Baseline and governed `azd` environment configuration.
- The admin-connected simulator model route through API Management.

The baseline will deliberately demonstrate specific governance gaps, including overprivileged identity, missing parameter-level authorization, missing approval enforcement, permissive egress, permissive execution budgets, and incomplete evidence.

It must remain safe for demonstration: use only synthetic data, controlled destinations, hard external spend limits, isolated resources, and an operator stop.

## Planned structure

```text
agent-under-test\
  azure.yaml
  agent-definition\
  tools\
  infra\
  config\
  synthetic-data\
  README.md
```

The planned `azd` environments are:

- `baseline`: intentionally weak governance configuration.
- `governed`: independently enforced protections.

Both environments must use the same Prompt Agent instructions, tools, simulator fixtures, and synthetic dataset. No agent, tool, infrastructure, configuration, or data artifacts have been added yet.
