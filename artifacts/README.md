# Hackathon Artifacts

This directory separates reusable framework components from the two environments used for the before-and-after demonstration.

```text
artifacts\
  reusable-components\
    model-simulator\
    campaign-orchestrator\
    contracts\
  agent-under-test\
    agent-definition\
    tools\
    infra\
    config\
    synthetic-data\
  agent-under-test-governed\
    config\
    policies\
    expected-controls\
```

`campaign-orchestrator` owns campaign execution, evidence collection, verdict evaluation, comparison, and report generation.

`agent-under-test` is the single `azd` project. It owns the shared Prompt Agent definition, tool APIs, Bicep infrastructure, synthetic data, and the `baseline` and `governed` Azure Developer CLI environments.

`agent-under-test-governed` contains the governed profile, policies, and expected control outcomes. It does not duplicate the Prompt Agent definition or Bicep deployment.

No implementation artifacts are present yet. The README files define component boundaries and comparison invariants for the spike.
