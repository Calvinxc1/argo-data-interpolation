# Governance Split Alignment Pass

Date: 2026-06-24

Scope: Repository structure after separating the active repo-local governance copy from the generalized lab governance copy.

## Observations

- `AGENTS.md` now identifies `.governance/` as the active local governance source for agents working in this repository.
- `README.md` now states the repository purpose and distinguishes the active local governance copy from the generalized lab governance copy.
- `.governance/` now contains local policy, process, routing, and override files that govern this repository the same way `.governance/` governs any other repository.
- `lab-governance/` now contains the generalized policy, process, routing, and override files intended to propagate to the lab.
- The two trees intentionally duplicate governance rules and may drift when the drift is visible and intentional.
- `.governance/local/` now records explicit local deviations from the generalized lab-governance rule set.
- `.governance/task-map.yaml` routes local work to `.governance/` paths.
- `.governance/policies/universal.yaml` routes additional local policy through `.governance/task-map.yaml`.
- `lab-governance/task-map.yaml` routes only to `lab-governance/` paths.
- `lab-governance/policies/universal.yaml` routes additional policy through `lab-governance/task-map.yaml`.
- Both policy-maintenance copies now require future governance edits to keep the duplicated-layer distinction and README files aligned.

## Alignment Findings

- Current trunk structure aligns with the intended duplicated two-layer model.
- Current active local policy loading routes through `.governance/`, as it should for repo-local agent behavior.
- Current generalized lab policy loading routes through `lab-governance/`, as it should for the propagated rule set.
- The closeout clarification is preserved in both `.governance/policies/inter-agent-communication.yaml` and `lab-governance/policies/inter-agent-communication.yaml`.
- The current trunk copies are intentionally aligned by content except for path references and documentation that distinguish their roles.
- Future drift should be reviewed explicitly rather than inferred from path differences.
- Local deviations identified from this repository's purpose are recorded in `.governance/local/deviations.yaml`.
- The current local deviations concern dual-tree governance maintenance, visible drift tracking, and branch distribution for kind-specific governance branches.
- Kind branches still need branch-local migration after trunk ratification so each branch has both an active `.governance/` local copy and a `lab-governance/` generalized copy.

## Follow-Up

- After Jason ratifies the trunk structure, commit the trunk migration.
- Merge trunk down into kind branches.
- On each kind branch, preserve `.governance/` as the active branch-local governance copy.
- On each kind branch, maintain `lab-governance/` as the generalized lab governance copy and update branch-local route references in each tree according to that tree's role.
