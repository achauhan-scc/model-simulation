# Expected Governed Controls

This directory will describe the controls that must be present and the evidence expected from the governed deployment.

Examples include:

- High-value refund requests require approval.
- Backend authorization denies unauthorized operations.
- Unapproved outbound destinations are blocked.
- Request and execution budgets stop excessive activity.
- Prompt Agent, gateway, tool, identity, and business events are correlated.
- An early block marks later controls as `Not exercised`.

The actual Azure resources are deployed from the shared Bicep project under `agent-under-test\infra`.

No expected-control definitions have been added yet.
