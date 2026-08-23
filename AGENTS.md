# AGENTS.md

Repository policy entrypoint. Active repo-local governance lives under `.governance/`.
The generalized lab-wide governance rule set maintained by this repository lives under `lab-governance/`.
The two trees intentionally duplicate policy and may drift; use `.governance/` to govern work in this repository unless a task explicitly concerns the generalized rule set.

Precedence:
`AGENTS.md` > `.governance/processes/*.yaml` > `.governance/policies/*.yaml` > `.governance/overrides/*`
If ambiguity remains, ask before acting. Override-governance rules are non-overridable unless a process file explicitly says otherwise.

Always load:
- `.governance/policies/universal.yaml`

Load additional policy only via:
- `.governance/task-map.yaml`
- `.governance/kind-routes.yaml` when present on a kind branch
