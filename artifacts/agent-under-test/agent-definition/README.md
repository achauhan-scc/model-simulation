# Shared Prompt Agent Definition

This directory will contain the declarative customer-support Prompt Agent definition used by both environments:

- Instructions.
- Tool declarations and schemas.
- Model deployment reference.
- Version metadata.
- Agent configuration required for repeatable deployment.

Maintain controlled agent variants with identical instructions and tools:

| Variant | Model | Environment |
|---|---|---|
| Real baseline | Real Foundry model | Baseline |
| Simulated baseline | Admin-connected simulator | Baseline |
| Simulated governed | Same admin-connected simulator | Governed |
| Real governed | Real Foundry model | Governed; optional |

The model reference and governance profile may differ. Instructions, tool definitions, fixture version, and synthetic data must remain identical for comparison.

No Prompt Agent definitions have been added yet.
