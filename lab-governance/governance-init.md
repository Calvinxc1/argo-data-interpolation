# Governance Initialization

Purpose: give a new agent enough procedure to initialize governance before doing substantive work.

This document is a setup guide, not a replacement for policy. The operative contract remains the repository or workspace governance files the agent loads during initialization.

## Startup Order

1. Find the workspace governance entrypoint.

   Start with `AGENTS.md` at the workspace root. If no workspace-local `AGENTS.md` exists, ask Jason or the orchestrating agent where governance is mounted before doing substantive work.

2. Load the always-load policy.

   Follow the entrypoint exactly. In this governance system, the normal always-load file is `.governance/policies/universal.yaml` for an active workspace copy, or `lab-governance/policies/universal.yaml` when initializing from the generalized lab governance source.

3. Load task-specific policy through the task map.

   Use `.governance/task-map.yaml` in an active workspace copy. Use `lab-governance/task-map.yaml` only when bootstrapping from the generalized source or maintaining generalized governance itself.

   If the task asks the agent to join, monitor, coordinate in, or close an Althing or other live agent room, select the `live_agent_coordination` route before joining the room.

4. Check branch or kind routing.

   If the active governance branch has a `.governance/kind-routes.yaml` file, load it after the task map. Trunk-general governance does not require a kind-routes file.

5. Prompt for the canonical agent name.

   Ask Jason or the orchestrating agent for the agent's Jason-settled canonical name before version reconciliation or substantive work. Use a direct prompt:

   ```text
   What canonical agent name should I use for this workspace?
   ```

   If a local self-stamp or registry row already names a canonical agent, report that value and ask Jason to confirm or correct it. Do not infer the canonical name from the repository name, hostname, model backend, task role, or prior chat label.

6. Check governance version state.

   Read the local self-stamp if present. The standard desktop-orchestrator self-stamp path is `.governance/local/version-stamp.yaml`. Compare the self-stamp against the central registry row when a registry is available.

   The central registry in this repository is `agent-registry/agents.yaml`, with schema in `agent-registry/schema.yaml`.

7. Apply the startup version rule.

   If current governance version equals target, continue silently. If current is behind target, report only:

   ```text
   Current: <version>
   Target: <version>
   Update before proceeding? yes/no
   ```

   Then wait for Jason's answer before substantive work.

   If Jason answers yes, use `lab-governance/templates/governed-agent-update-prompt.md` from the ai-governance repository as the canonical update prompt. Follow that prompt for source branch selection, local governance update, self-stamp update, reconciliation reporting, and registry-loop attestation.

8. Declare loaded governance if action will follow.

   Before edits, connector actions, or other substantive work, state the intended action, affected files or systems, expected risk tier, and validation plan unless Jason's latest message already clearly authorized immediate execution.

## Althing And Live Room Join Checklist

Before joining an Althing or other live agent room:

- Load the `live_agent_coordination` route and the room transport's available connector boundaries.
- Know the room identifier, canonical agent name, assigned or expected role when one was provided, and any Jason-designated runner, closer, or liaison.
- Announce presence in one line after joining.
- Check current presence if the transport supports it.
- Participate in the preliminary coordination exchange before substantive room work begins.
- Keep cursor-aware polling active while the room remains active.
- Do not leave until suspended, closed out, or dismissed by name.

## Installing Governance Into A New Workspace

Use this sequence when an agent workspace does not yet have a local governance copy.

1. Identify the intended agent kind and source branch.

   First ask for the workspace's canonical agent name. Use the registry when present. If no registry row exists, ask Jason before choosing a governance branch or kind.

2. Copy the branch-local governance picture into the workspace.

   A governed workspace should have a local `.governance/` tree and an `AGENTS.md` entrypoint. Do not point ordinary workspace agents directly at this repository's `.governance/` tree unless Jason explicitly chooses a centralized mount model for that workspace.

3. Preserve the entrypoint contract.

   `AGENTS.md` should stay thin. It should name the active governance directory, precedence order, always-load file, and routing files.

4. Create or update the local self-stamp.

   Start from `lab-governance/templates/agent-self-stamp.yaml`. Fill only locally attested values. Use `null` rather than invented data.

5. Reconcile registry and self-stamp state.

   If the registry and self-stamp disagree, do not silently choose one. Mark the state as `behind`, `drifted`, or `unknown` as appropriate, then route the decision to Jason through the active human liaison.

6. Confirm no secrets were introduced.

   Governance files may contain paths, branch names, canon versions, and provenance references. They must not contain tokens, API keys, private credentials, or recoverable secrets.

## Minimum Files For A Governed Workspace

The normal local workspace shape is:

```text
AGENTS.md
.governance/README.md
.governance/task-map.yaml
.governance/branch-descriptor.yaml
.governance/policies/universal.yaml
.governance/policies/*.yaml
.governance/processes/*.yaml
.governance/overrides/*.yaml
.governance/local/version-stamp.yaml
```

Kind branches may add:

```text
.governance/kind-routes.yaml
```

This `ai-governance` repository also maintains:

```text
lab-governance/
agent-registry/
canon-version-log/
```

Ordinary downstream repositories should not infer that they need to maintain those generalized governance maintenance trees locally.

## Acceptance Checklist

Governance is initialized when all of the following are true:

- The agent knows which governance entrypoint governs the workspace.
- The agent has asked for, confirmed, or explicitly reported as missing its Jason-settled canonical name.
- The agent has loaded `AGENTS.md` and the always-load policy.
- Additional policy was loaded only through the task map and any kind route.
- The agent has checked self-stamp and registry state when those records exist.
- Any version mismatch was reported using the minimal startup version rule.
- The agent can name the active canon version it believes it is consuming, or can clearly state that the value is unknown.
- The agent has not written secrets into governance files.
- Jason remains the final arbiter for unresolved human-owned decisions.

## Failure Modes

Stop and ask before substantive work when:

- No governance entrypoint can be found.
- The Jason-settled canonical agent name is missing or disputed.
- The active branch, kind, or target canon version is ambiguous.
- Registry and self-stamp state disagree.
- A policy conflict changes whether the agent may act.
- The requested task depends on accepting a draft governance rule as ratified.

When blocked, report the exact missing fact or conflict. Do not continue by treating silence, draft text, or execution permission as acceptance.
