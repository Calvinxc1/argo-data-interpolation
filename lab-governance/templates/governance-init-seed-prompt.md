# Governance Init Seed Prompt

Use this prompt when starting a new agent that needs to initialize governance.

```text
Before doing substantive work, initialize governance for this workspace.

Start by reading AGENTS.md at the workspace root. Follow its precedence order, always-load policy, task-map routing, and any kind-route instructions. If this workspace does not yet have local governance, use the setup guide at lab-governance/governance-init.md from the ai-governance repository to install or verify the local governance copy before acting.

If this task asks you to join, monitor, coordinate in, or close an Althing or other live agent room, select the `live_agent_coordination` route before joining the room. Before calling a room join operation, know the room identifier, canonical agent name, assigned or expected role when one was provided, any Jason-designated runner, closer, or liaison, and the obligation to maintain cursor-aware polling until suspended, closed out, or dismissed by name.

Before checking versions or doing substantive work, ask:

What canonical agent name should I use for this workspace?

If a self-stamp or registry row already names a canonical agent, report that value and ask Jason to confirm or correct it. Do not infer the canonical name from the repository name, hostname, model backend, task role, or prior chat label.

Check the local self-stamp if one exists. Check the central registry if available. If current governance version equals target, continue silently. If current is behind target, report only:

Current: <version>
Target: <version>
Update before proceeding? yes/no

Then wait for Jason's answer before substantive work.

Do not write secrets into governance files. Do not treat draft text, silence, or execution permission as acceptance. When initialization is complete, state the canonical agent name or unresolved missing-name status, loaded entrypoint, active governance source, active canon version or unknown value, and any unresolved drift.
```
