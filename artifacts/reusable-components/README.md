# Reusable Components

This directory contains the reusable capabilities that form the product spike:

- `model-simulator`: exposes deterministic hostile responses through an OpenAI-compatible Chat Completions endpoint.
- `campaign-orchestrator`: runs scenarios, preserves run state, collects and normalizes evidence, evaluates controls, compares runs, and generates reports.
- `contracts`: defines the versioned schemas shared by all components.

These components must remain independent of the Contoso refund storyline wherever practical. Demo-specific behavior belongs in scenario and environment manifests rather than hard-coded component logic.
