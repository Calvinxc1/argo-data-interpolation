# Repo-Local Governance Copy

This directory is this repository's active local governance copy.

Agents working in this repository load and follow this directory the same way they would use `.governance/` in any other repository. `AGENTS.md` points here for the active local policy contract.

Committed governance files under `.governance/` are ratified by existence. Status fields may still describe operational role, such as `active`, but they are not a separate ratification gate. Draft local-governance proposals must stay outside this active local governance tree until Jason ratifies them.

Use `task-map.yaml` as the explicit loading contract. It may define reusable route groups, but agents should still load only the groups and direct files named by selected routes instead of scanning policy folders.

This directory intentionally duplicates governance rules that may also appear in `lab-governance/`. Drift is allowed when it is visible and intentional:

- `.governance/` governs this repository's work.
- `lab-governance/` is the generalized rule set maintained here for propagation to other agents and repositories.

Use `local/` for explicit repo-local deviations from the generalized rule set. Use `records/` for repo-local alignment notes or operational metadata. If a local rule should become general lab governance, promote it through an explicit `lab-governance/` policy or process change.
