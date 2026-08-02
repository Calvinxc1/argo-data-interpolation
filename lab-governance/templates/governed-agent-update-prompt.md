# Governed Agent Update Prompt

Use this prompt when a governed agent needs to update its local governance copy from the ai-governance Gitea repository.

Canonical source:

```text
gitea.infra.newedenhomestead.net:ai-projects/ai-governance.git
```

Canonical prompt path:

```text
lab-governance/templates/governed-agent-update-prompt.md
```

## Prompt

```markdown
You are updating your local governance copy from Jason's ai-governance repository.

If you do not already have a Jason-settled canonical agent name, stop before changing files and ask:

    What canonical agent name should I use for this workspace?

If a local self-stamp or registry row already names a canonical agent, report that value and ask Jason to confirm or correct it. Do not infer the canonical name from the repository name, hostname, model backend, task role, or prior chat label.

Before changing files, identify and report:

- Your Jason-settled canonical agent name.
- Your agent kind.
- Your current local governance source path.
- Your current local self-stamp path, if present.
- Your current active canon version and generalized canon version, if known.
- The target active governance branch from `agent-registry/agents.yaml`, if a row exists.
- The target active canon version and target generalized canon version from `agent-registry/agents.yaml`, if a row exists.

Then perform the update carefully:

1. Fetch or inspect the ai-governance Gitea repository.
2. Select the active governance branch for your agent kind or registry row.
3. Record the source commit SHA and branch you are consuming.
4. Compare the source branch descriptor against your local self-stamp and registry row.
5. Report any reconciliation issue before mutating local files, including branch mismatch, canon-version mismatch, missing self-stamp, unknown registry row, or local-only governance files.
6. Copy or merge the appropriate governance files into your local workspace.
7. Preserve local-only governance files unless Jason or an explicit policy says to reconcile them.
8. Update your local self-stamp with canonical agent name, agent kind, active governance branch, active canon version, generalized canon version, canon-version log reference, source commit, source repository or path, timestamp, declared status, and notes.
9. Re-read the updated entrypoint and required governance files.
10. Report any remaining reconciliation issue after the update.

After updating, create a structured registry attestation. Use this shape:

    type: agent_registry_attestation
    canonical_agent_name: null
    agent_kind: null
    active_governance_branch: null
    source_repository: gitea.infra.newedenhomestead.net:ai-projects/ai-governance.git
    source_commit: null
    previous_active_canon_version: null
    current_active_canon_version: null
    previous_generalized_canon_version: null
    current_generalized_canon_version: null
    self_stamp_path: null
    self_stamp_updated: null
    registry_loop_transport: null
    registry_loop_result: null
    updated_at: null
    result: null
    reconciliation:
      - null

Submit the attestation through the currently ratified registry-loop transport when available. If no transport is available, write the attestation to a local durable path and report that path. Do not directly edit `agent-registry/agents.yaml` unless a ratified process explicitly authorizes direct registry mutation.

Close out by reporting:

- Source branch and commit consumed.
- Active and generalized canon versions after update.
- Self-stamp path updated.
- Registry attestation path or submission target.
- Whether the central registry is updated, pending, failed, or explicitly deferred.
- Any unresolved reconciliation item and its owner.
```
