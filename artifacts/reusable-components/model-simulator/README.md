# Scenario-Driven Model Simulator

## Purpose

Provide a generic, deterministic model double for authorized assumed-compromise campaigns. The simulator will be exposed to Foundry as an admin-connected model through API Management.

The simulator is one web application with a data-driven behavior layer. It is not intended to emulate a complete language model.

```text
Prompt Agent request
  -> POST /chat/completions
  -> protocol validation
  -> model-profile resolution
  -> deterministic request matching
  -> response-fixture rendering
  -> OpenAI-compatible response
  -> simulator evidence event
```

The simulator will not execute tools, override the agent runtime, change permissions, or bypass controls under test.

## API surface

Required endpoint:

```http
POST /chat/completions
```

The initial implementation will support the subset required by the Prompt Agent:

- `model`
- `messages`
- `tools`
- `tool_choice`
- Text responses
- Structured `tool_calls`
- Tool-result messages in later turns
- Clearly labelled synthetic `usage`
- `stream` only if required by the selected Prompt Agent path

Operational endpoints:

```http
GET /healthz
GET /readyz
GET /admin/scenarios
GET /admin/scenarios/{id}
```

Administrative endpoints are initially read-only. The spike will not accept arbitrary runtime response uploads.

## Foundry connection

The planned route is:

```text
Prompt Agent
  -> admin-connected model deployment
  -> API Management
  -> model simulator
```

API Management will authenticate the Foundry project, restrict direct simulator access, apply test-safe limits, and capture gateway evidence. The Prompt Agent will select the simulator by its connected deployment name.

## Scenario selection

The `model` field will select a versioned simulator profile:

```text
hostile-refund-v1
hostile-egress-v1
hostile-budget-v1
hostile-chain-v1
```

Model aliases are configured through the admin-connected model deployment. An arbitrary end-user header must not activate or select hostile simulation behavior.

Each model profile points to a scenario mapping. A mapping:

- Validates the expected conversation stage.
- Confirms required tool definitions are present.
- Matches stable synthetic identifiers or prior tool results.
- Selects an immutable response fixture.
- Declares the evidence event to emit.
- Rejects ambiguous or unmatched requests.

The initial matcher should use exact or simple deterministic rules. It should not use an LLM, semantic similarity, arbitrary scripts, or unbounded regular expressions.

## Multi-turn behavior

Prefer stateless matching against the complete Chat Completions message history:

```text
initial request
  -> request customer record

customer-record tool result
  -> request high-value refund

refund tool result
  -> request controlled exfiltration
```

If minimal state is later required, it must be keyed by an authorized campaign run identifier. Simulator state is never evidence that a tool or business operation occurred; authoritative outcome evidence comes from the agent, tool API, or controlled destination.

## Evidence

Every response should emit a sanitized, append-only event containing:

- Timestamp.
- Campaign run identifier, when available.
- Scenario and model-profile identifiers.
- Matched rule and response-fixture identifiers.
- Requested and emitted tool names.
- Synthetic usage classification.
- Request and response hashes.

Do not store full prompts by default. Full-content retention requires explicit campaign configuration.

## Security boundaries

- Restrict access through API Management.
- Authenticate the Foundry project or approved caller identity.
- Use reviewed, version-controlled fixtures only.
- Reject unknown model aliases and unmatched requests.
- Limit request rate, duration, and response size.
- Provide an operator disable mechanism.
- Never use real customer data or production credentials.
- Do not expose a general-purpose API for uploading arbitrary hostile responses.

## Folder structure

```text
model-simulator\
  src\
    api\
    protocol\
    resolver\
    matching\
    rendering\
    telemetry\
    security\
  mappings\
    scenarios\
  responses\
  schemas\
  tests\
    contract\
    mappings\
    fixtures\
  README.md
```

Planned root implementation artifacts include the language-specific dependency manifest and a `Dockerfile`. No simulator implementation, mappings, schemas, response fixtures, or tests have been added yet.
