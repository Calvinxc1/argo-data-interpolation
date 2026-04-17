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

Repo-specific notebook policy:
- For Jupytext-paired notebooks, if an `.ipynb` and its matching `.py` differ and notebook work is requested, sync the `.py` from the notebook state first.
- After that sync, make edits in the `.py` file rather than editing the `.ipynb` directly.
- Do not overwrite or sync changes back into the `.ipynb` unless the user explicitly asks for that step.
