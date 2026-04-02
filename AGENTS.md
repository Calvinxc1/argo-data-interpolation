# AGENTS.md

Repository policy entrypoint. Authoritative policy lives under `.governance/`.

Precedence:
`AGENTS.md` > `.governance/processes/*.yaml` > `.governance/policies/*.yaml` > `.governance/overrides/*`
If ambiguity remains, ask before acting. Override-governance rules are non-overridable unless a process file explicitly says otherwise.

Always load:
- `.governance/policies/universal.yaml`

Load additional policy only via:
- `.governance/task-map.yaml`

Repo-specific environment note:
- This repository uses `uv` for its development environment.
