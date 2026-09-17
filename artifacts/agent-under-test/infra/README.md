# Shared azd and Bicep Infrastructure

This directory will contain one parameterized Bicep deployment for both the baseline and governed `azd` environments.

Planned resources include:

- Foundry account and project.
- Prompt Agent dependencies.
- Real model deployment.
- API Management.
- Admin-connected simulator model deployment.
- Simulator hosting.
- Synthetic tool APIs and controlled destination.
- Managed identities and role assignments.
- Application Insights and Log Analytics.
- Optional network, content-safety, and detection resources.

The Bicep entry point will accept a governance profile such as `baseline` or `governed`. The baseline preserves hackathon safety boundaries while omitting or weakening selected governance controls. The governed profile enables the protections declared under `agent-under-test-governed`.

Use:

```powershell
azd up
```

for the initial or complete deployment, `azd provision` for Bicep-only changes, and `azd deploy` for deployable service-code changes.

No infrastructure artifacts have been added yet.
