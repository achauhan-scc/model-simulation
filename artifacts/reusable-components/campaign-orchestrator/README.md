# Campaign Orchestrator

## Purpose

Execute an authorized scenario against a selected environment, preserve the evidence required to reproduce the result, evaluate the tested controls, and generate the assurance report.

The orchestrator will:

- Validate scenario and environment manifests.
- Run preflight checks.
- Generate a unique run identifier.
- Select the appropriate version-controlled Prompt Agent definition:
  - Real-model baseline
  - Simulated-model baseline
  - Simulated-model governed
  - Optional real-model governed
- Capture pre-run and post-run business state.
- Invoke the agent under test.
- Collect evidence through adapters.
- Mark controls that were excluded or not reached.
- Normalize and correlate collected evidence.
- Calculate control and coverage verdicts.
- Generate HTML, Markdown, JSON, and optional SARIF reports.
- Persist an immutable run bundle.
- Compare baseline and governed runs.

Scheduling is a later capability. Reliable execution, evidence collection, and comparison are the spike priorities.

The orchestrator must not let an arbitrary end-user header enable simulation. Model selection is controlled through approved Prompt Agent definitions and campaign configuration.

## Internal processing boundary

```text
campaign execution
  -> immutable run bundle
  -> evidence normalization
  -> correlation
  -> control evaluation
  -> report rendering
```

Reporting consumes the persisted run bundle rather than temporary execution state. This allows reports to be regenerated without rerunning a campaign and preserves a future extraction boundary.

Supported verdicts will be `Passed`, `Failed`, `Not exercised`, `Inconclusive`, and `Not applicable`. Missing evidence must not produce a passing verdict.

## Planned structure

```text
campaign-orchestrator\
  src\
    cli\
    engine\
    evidence\
    evaluation\
    reporting\
    storage\
  campaigns\
  environments\
  templates\
  tests\
  README.md
```

No orchestrator implementation, campaign definitions, adapters, templates, or generated reports have been added yet.
