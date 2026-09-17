# Run Storage

This directory will implement the filesystem-based run store.

Each run will use immutable JSON snapshots, an append-only JSONL event journal, an evidence index, verdict files, and generated reports. Credentials and secrets must not be persisted.

No run-store implementation has been added yet.
