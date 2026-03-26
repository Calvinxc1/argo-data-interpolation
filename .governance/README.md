# .governance

This directory contains the repository's governance corpus.

## Layout

- `policies/`: standing repository policies grouped by domain, stored as YAML.
- `task-map.yaml`: task-to-policy routing map for selective loading.
- `processes/`: governance-process rules such as override handling and policy maintenance, stored as YAML.
- `overrides/`: structured override records and the schema governing those records.

## Authoritative Files

The repository policy entrypoint is [../AGENTS.md](../AGENTS.md). The files under this directory are the machine-readable policy body that `AGENTS.md` points to.

## Guidance

- Keep standing policy in `policies/`.
- Keep task routing in `task-map.yaml`.
- Keep meta-governance and maintenance rules in `processes/`.
- Keep temporary exception records and their data definitions in `overrides/`.
- When policy structure changes, update `AGENTS.md` and this directory together.
