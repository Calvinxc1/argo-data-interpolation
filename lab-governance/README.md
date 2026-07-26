# Lab Governance Layout

This directory contains the lab-wide governance rule set maintained by this repository.

These files are the general policy and process contract intended to propagate to the rest of the lab and to specialized agent branches.

This directory is not the active local governance entrypoint for agents working in this repository. That role belongs to `.governance/`. The two trees intentionally duplicate governance rules and may drift when the distinction is visible and intentional.

The trunk branch carries the general contract for every agent kind. Kind branches carry complete branch-local pictures after trunk is merged down into them. Core content is intentionally duplicated across kind branches so an agent can read one branch and have the complete contract.

Layout:

- `AGENTS.md`: thin entrypoint with precedence, always-load policy, and routing pointer.
- `lab-governance/governance-init.md`: setup guide for initializing governance in a new or unverified agent workspace.
- `lab-governance/task-map.yaml`: task or session routing to the additional policy files that should be loaded. Route groups provide reusable subroutes; selected routes, not folder names, remain the explicit loading contract.
- `lab-governance/policies/`: standing domain policies in YAML.
- `lab-governance/processes/`: meta-governance and operating processes.
- `lab-governance/overrides/`: temporary exception log and its schema.
- `lab-governance/templates/`: reusable setup templates, including the local self-stamp template and governance init seed prompt.
- `lab-governance/templates/governed-agent-update-prompt.md`: canonical governed-agent update prompt for local governance copies, self-stamps, reconciliation feedback, and registry-loop attestation.

Kind branches add `lab-governance/branch-descriptor.yaml` and `lab-governance/kind-routes.yaml`. Trunk does not carry those files, so trunk merge-downs do not overwrite kind orientation or kind-specific routing.
