# azd Environment Configuration

This directory will document values required by the two `azd` environments:

- `baseline`
- `governed`

Environment-specific values will be stored through `azd env set` and resolved from `.azure\<environment>\.env`. The selected environment will supply the governance profile, resource names, endpoints, model deployment references, and feature switches used by Bicep and deployment.

Secrets and credentials must not be committed. No configuration artifacts have been added yet.
