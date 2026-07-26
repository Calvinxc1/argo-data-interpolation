# Education Research Handoff

Date: 2026-06-29
Room: education-research-handoff
Participants observed: Education, Personal, Career, Codex
Status: relocation recorded; communication-policy recommendations ratified and promoted; UQ boundary recommendation pending Jason ratification

## Scope

This record captures the durable governance side of the live Althing room
`education-research-handoff`.

The live room is non-durable. This file is the hand-written durable record.
Agent convergence is a recommendation only. No governance boundary or policy
change in this record is canon until Jason explicitly ratifies it.

## Relocation Status

Completed in-room on 2026-06-30.

Education is coordinating the 2026-06-29 standup relocation in which Education
becomes the source of truth for schooling and Argo research substance, while
Personal and Career demote their retained material to pointers.

Education confirmed receipt and write of:

- Personal `Education (SFCC to OSU).md`, written at the Education root.
- Personal `Oceanography (Argo).md` research substance, written at
  `Education/research/Oceanography Argo (research).md`.
- Career `main.tex` and `references.bib`, written at
  `Education/research/paper/`.
- Career `argo-community.yaml`, written at
  `Education/research/argo-community.yaml`.

Personal confirmed demotion of its source copies to pointers:

- `Research & Education/Education (SFCC to OSU).md` is now a thin pointer to
  Education, retaining only the one-line ABET/EAC ME degree rationale.
- `Research & Education/Oceanography (Argo).md` is now a one-line passion
  pointer to Education for research substance and Career for career-facing
  items.
- Personal updated its `deviations.yaml` folder-scope handoff,
  `knowledge-map.md`, and the maritime pathway pointer.

Career confirmed demotion of its source copies to pointers:

- `papers/ieee-oceans-2026/main.tex` and `references.bib` are now thin
  pointers to `Education/research/paper/`.
- `reference/background/argo-community.yaml` is now a thin pointer to
  `Education/research/argo-community.yaml`.
- Career retained career-instrumental items: engagement strategy, calendars,
  networking and contacts, opportunity venues, and role-targeting references.
- Career updated its knowledge map from pending to relocation-complete.

## UQ Repository Boundary Recommendation

Recommended for Jason ratification:

- The GitHub repository holding the UQ library code belongs to the Coding Agent
  domain for code stewardship.
- Code stewardship includes repository hygiene, packaging, tests, CI, issues,
  releases, dependency and security maintenance, and implementation changes.
- Education owns the research substance expressed by the project.
- Research substance includes schooling context, Argo/UQ methodology, paper
  text, scientific rationale, literature, interpretation, and domain-facing
  conclusions.
- Coding Agent may implement Education-ratified research requirements, but
  Coding Agent is not the source of truth for the research content.
- Career and Personal should retain pointers only where they need workflow
  context.

Education accepted this recommendation in-room for routing to Jason.

Education also recorded an implementation split for the UQ repo:

- `main.tex`, `references.bib`, and `argo-community.yaml` are research
  substance and should transfer to Education.
- `render_paper.py` and compiled PDFs are build tooling and stay on the code
  side.
- `jana_remake_image.jpg` is a deferred file-level copy because it is too large
  for a text transcript. It remains with the repo assets under the Coding Agent
  boundary unless Jason decides Education needs a copy.

Career later flagged that `papers/ieee-oceans-2026/render_paper.py` embeds the
full paper prose inline as ReportLab strings. It therefore remains on the code
side under the parked Coding Agent boundary, but it is a latent divergent copy
of Education's canonical research substance and should be reconciled against
Education's source of truth when the repo boundary is taken up.

## Althing Presence Recommendation

Education raised a governance recommendation from the 2026-06-29 standup:
agents' Althing sessions expired on the roughly 15-minute presence window and
went silent before closer-led closeout.

Recommended for Jason ratification:

- While a room task is open, each participant keeps presence alive by rejoining
  or polling before expiry until the closer signals closeout.
- An agent that must leave before closeout posts an explicit suspend notice
  with a resume trigger and owner, rather than allowing silent expiry.
- The primary agent or closer is responsible for properly dismissing every
  participant by name once that participant's contribution is authentically
  finished.
- Participants do not self-exit before that explicit dismissal. An unannounced
  departure is treated as a failure state, not a tidy exit.
- While awaiting dismissal, each participant actively maintains presence by
  rejoining or re-polling before expiry.
- A dismissed participant posts an explicit acknowledgment to its by-name
  dismissal before leaving.
- Absence of a dismissal acknowledgment, or disappearance before dismissal, is a
  failure state requiring the closer to log the participant as an unconfirmed
  exit.
- An agent that explicitly acknowledges it is awaiting dismissal and then stops
  active monitoring before dismissal commits a distinct failure: it broke an
  explicit commitment to keepalive, not merely a passive presence expiry.
- By-name dismissal requires per-logical-agent identity. Two logical agents
  must not share one visible sender name and participant identity when they need
  to be dismissed separately.
- The closer stands down last, after the post-closeout presence check.
- Re-waking a dropped agent costs a human-liaison round, so keepalive is the
  default rather than wake-on-demand.

Jason ratified the presence, liaison, canonical-name, slower-agent liveness,
multipart-transfer, and dismissal/closeout recommendations after this handoff.
They were promoted into:

- `.governance/policies/inter-agent-communication.yaml`
- `lab-governance/policies/inter-agent-communication.yaml`

## Althing Connector Diagnosis

Status: confirmed in-room; local fixes reported; deployment pending Jason
ratification.

During the handoff, agents observed live Althing connector failures:

- `await_messages` with longer timeouts returned MCP host timeouts or nginx
  HTTP 504 rather than the documented empty-on-timeout broker response.
- Participant-scoped calls failed with messages such as `no participant named X
  is joined` after timeout, process change, or short gaps.
- One visible sender name, `Codex`, was shared across two logical agents,
  making transcript attribution ambiguous.
- The 8192-character post body cap forced large file transfers into manual
  multi-part splits.

Education, as liaison, recorded the converged diagnosis:

- Root Cause A: long-poll calls can be killed by the MCP host or proxy before
  the broker returns. Reported local fix: cap each broker await at
  `ALTHING_AWAIT_BLOCK_TIMEOUT_S`, default 45 seconds, and return an empty
  result with unchanged cursor on timeout so callers re-arm cleanly.
- Root Cause B: `no participant named X is joined` has two causes. First,
  connector-local state loss when a different or restarted connector process
  lacks the in-memory name-to-participant mapping. Reported local fix:
  participant-scoped `post` and `await_messages` with `name=` auto-join when
  local mapping is missing. Second, true stale broker sessions. Reported local
  fix: raise broker presence TTL from 900 seconds to 3600 seconds, let
  participant-scoped `history`, `who`, and `who_sessions` refresh presence, and
  auto-rejoin once on stale participant before retrying.
- Root Cause C: visible sender-name sharing across logical agents makes
  transcript attribution ambiguous. Recommendation: use a distinct
  `participant_id` per logical agent and, where appropriate, a distinct
  canonical name, even when agents share a connector process. This is also a
  closeout requirement: a closer cannot dismiss or confirm logical agents
  individually when multiple agents share one visible identity.

Validation reported by the diagnostic agent:

- `uv run pytest`: 42 tests passed.
- `uv run ruff check`: passed.
- README updated with the new defaults and configuration.

Deployment status:

- Fixes were reported as applied in the local Althing repository.
- They were not yet deployed to the live MCP or broker runtime at the time of
  this record.
- Jason ruled that live deployment is handed off to his direct session with the
  Althing coding agent, not driven from the `education-research-handoff` room.
- Jason later ratified the communication-policy recommendations captured in
  this record. They were promoted into the active repo-local policy and the
  generalized lab-governance copy.
