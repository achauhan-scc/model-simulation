# Shared Contracts

This directory will hold the versioned contracts shared by the simulator, campaign orchestrator, environments, evidence adapters, evaluation logic, and report generators.

Planned schemas:

- `scenario.schema.json`: hostile response, expected path, and expected stop point.
- `environment.schema.json`: endpoints, identities, campaign mode, and evidence sources.
- `evidence.schema.json`: normalized events and evidence references.
- `verdict.schema.json`: outcomes, exercised controls, gaps, and supporting evidence.

Schema files have not been created yet. Contracts should be defined before implementing the two reusable components.
