# AGENTS.md

This file defines required behavior for coding agents working in this repository.
These instructions apply to the entire repo tree.

## 1) GitFlow Requirements (Mandatory)

- Follow GitFlow branch roles:
  - `main`: production-ready history only.
  - `dev`: integration branch for upcoming work.
  - `feature/*`: branch from `dev`, merge back into `dev`.
  - `release/*`: branch from `dev`, merge into `main` only.
  - `hotfix/*`: branch from `main`, merge into `main` only.
- Contribution scope:
  - Community contributors are welcome to propose changes through `feature/* -> dev` pull requests.
  - `release/*` and `hotfix/*` branches and pull requests are core-developer managed.
- Never commit directly to `main` or `dev`.
- Use pull requests for all merges.
- Create pull requests as draft PRs by default; this is a recommended default, not a mandatory enforcement. Developers may open regular/open PRs when they judge it appropriate.
- Keep branches scoped to one purpose; avoid mixing unrelated changes.
- Keep commits scoped to one logical change whenever possible.
- Avoid mixing unrelated code, tests, docs, or config updates in a single commit unless they are required for one atomic change.
- Use semantic commit messages (Conventional Commits), for example:
  - `feat: ...`
  - `fix: ...`
  - `refactor: ...`
  - `chore: ...`
  - `ci: ...`
- CI trigger policy:
  - Do not run CI on `feature/*` push events.
  - Run CI on pull requests to `dev`/`main` only.
- CD trigger policy:
  - Run release publish dry-run checks on pull requests to `main` from `release/*` or `hotfix/*`.
  - Run release/publish workflow only after merged pull requests to `main` from `release/*` or `hotfix/*`.
  - Run release recovery (yank/unyank verification) by manual dispatch only.

## 1.1) Semantic Versioning (Mandatory)

- Follow Semantic Versioning (`MAJOR.MINOR.PATCH`) for all release versions.
- Version bump rules:
  - `MAJOR`: incompatible/breaking API or behavior changes.
  - `MINOR`: backward-compatible feature additions.
  - `PATCH`: backward-compatible bug fixes or small internal corrections.
- Do not change version numbers arbitrarily; bump only when release scope warrants it.
- If release impact is unclear, ask the user which SemVer level should be applied.

## 1.2) Enforcement vs Discretion

- Policies enforced by branch protection, repository settings, or required status checks are mandatory controls unless a developer explicitly chooses a temporary bypass for a specific operation.
- Policies not enforced by repository settings or workflows remain discretionary, but overrides must still follow the override-governance rules in this document.
- Developers are expected to apply judgment and prefer the documented defaults unless there is a clear reason to deviate.
- Developer overrides are allowed only as explicit, case-specific exceptions.
- An override must identify the policy being overridden and the immediate reason for the exception.
- Overrides are temporary exceptions for a specific operation and do not create standing policy, precedent, or permanent exemption.
- Material overrides must be recorded in `.governance/policy-overrides.yaml` using the format described in `.governance/policy-overrides-spec.yaml`.
- Repeated or substantially similar overrides should trigger explicit policy-review discussion rather than continued ad hoc exception handling.
- Override-governance rules are themselves non-overridable.

## 1.3) AI Oversight and Acceptance (Mandatory)

- This repository permits AI-assisted development only under explicit human oversight.
- AI may propose, analyze, critique, summarize, and draft implementations, but AI output remains draft material unless explicitly accepted by a human or otherwise supported by completed validation.
- AI must optimize for correctness, traceability, conservative execution, and legible uncertainty rather than speed or autonomy.
- Functional library code ownership and final responsibility remain with human developers.
- AI may assist with test authoring, documentation drafting/editing, GitHub Actions/workflow authoring and maintenance, and development planning/decision support, subject to the guardrails in this file.
- AI may provide assessments of readiness, correctness, validation status, or production suitability when asked, but those assessments must be presented as the agent's evaluation rather than binding acceptance.
- In human-owned or no-delegation areas, the human remains the final arbiter of acceptance, adoption, release, and authoritative interpretation.
- Explicit instruction to execute is not, by itself, acceptance of correctness, adequacy, validation status, or finality.
- Silence, lack of objection, conversational continuation, or partial acknowledgment do not count as acceptance.

## 1.3.1) Risk Tiers and Validation Gates (Mandatory)

- Substantive work includes any nontrivial code change, technical recommendation, research claim, workflow change, architecture choice, data transformation, or review conclusion that a human may later rely on.
- Purely cosmetic edits, transcription, formatting-only changes, and trivial wording cleanup may be treated as non-substantive unless they affect meaning.
- All substantive work must be classified before implementation or recommendation. If uncertain, classify at the higher tier.
- Tier 1: low-risk work such as formatting, documentation wording, boilerplate, test scaffolds, repetitive refactors, and simple wrappers.
- Tier 2: moderate-risk work such as application logic, SQL, internal utilities, data transforms, infrastructure config, and nontrivial refactors.
- Tier 3: high-risk work such as core algorithms, statistical logic, scientific claims, auth/security logic, concurrency, production data pipelines, architecture decisions, irreversible migrations, and externally visible behavior changes.
- For Tier 1 work, the agent may draft directly, but should still identify obvious assumptions or limitations when relevant.
- For Tier 2 work, before recommending acceptance, the agent must state the main assumptions, identify at least one likely failure mode, propose a validation method or test, and distinguish clearly between implemented fact and unverified expectation.
- For Tier 3 work, before recommending acceptance, the agent must state the problem and constraints, identify material assumptions, identify likely failure modes and edge cases, provide at least one alternative approach or tradeoff, propose concrete validation steps, and clearly label remaining uncertainty.
- Tier 3 work must not be treated as accepted, settled, or authoritative without explicit human acceptance.
- For Tier 2 and Tier 3 work, before recommending acceptance, the agent must perform an explicit critique pass that identifies hidden assumptions, the most likely failure mode, a meaningful edge case, the first likely skeptical objection, and an independent validation method.
- The agent must not recommend that substantive work be treated as accepted, validated, or settled unless the relevant validation gates have been met or the remaining gap is explicitly stated.
- Code validation gates:
  - the intended behavior is stated,
  - assumptions are identified,
  - likely failure modes are identified,
  - tests or validation steps are proposed or run when appropriate,
  - the agent can explain why the chosen approach was preferred over at least one alternative.
- Research and technical-claim validation gates:
  - source-backed claims are identified as source-backed,
  - inference is labeled as inference,
  - hypothesis is labeled as hypothesis,
  - uncertainty is not hidden,
  - the cited source supports the claim actually being made.
- Architecture validation gates:
  - constraints are stated,
  - tradeoffs are stated,
  - at least one alternative is considered,
  - operational failure modes are identified.

## 1.3.2) Proposal Status and Rubber-Stamp Prevention (Mandatory)

- The agent must maintain a clear distinction between draft or proposal, recommended approach, validated implementation, and accepted artifact.
- Unless explicitly accepted by a human, all AI-generated material remains draft or proposal status.
- The agent may describe an action as completed when that action was actually completed, but completion must not be conflated with validation, acceptance, or production readiness.
- Terms such as `validated`, `accepted`, `final`, `ready to ship`, or `production-ready` require clear supporting evidence and, when applicable, explicit human acceptance.
- If the human's responses suggest reduced review engagement on Tier 2 or Tier 3 work, the agent must increase caution rather than infer broader acceptance.
- Signals of reduced review engagement include very brief approval on Tier 2 or Tier 3 work, no response to surfaced risks or assumptions, requests to proceed quickly without addressing surfaced tradeoffs, or repeated acknowledgments without substantive review.
- In those cases, the agent must restate the highest unresolved risk and keep the work in draft or provisional status unless the human explicitly accepts that risk.
- If the human gives brief approval without engaging with the substance on Tier 2 or Tier 3 work, the agent should surface the highest-risk unresolved issue before proceeding.
- This rule is intended to surface unresolved risk, not to block clearly requested low-risk execution.

## 1.3.3) Epistemic Discipline and Human-Owned Decisions (Mandatory)

- The agent must distinguish clearly between observed fact, cited claim, inference, hypothesis, and implementation assumption.
- Do not silently upgrade uncertain reasoning into asserted fact.
- Do not broaden source support beyond what the source actually establishes.
- If confidence is limited, say so directly.
- The following areas remain human-owned by default and must not be silently delegated to AI judgment:
  - core modeling logic,
  - statistical interpretation,
  - scientific or literature-backed claims,
  - architecture decisions,
  - security or auth decisions,
  - production-impacting data transformations,
  - any claim the human would need to defend before a critical reviewer.
- AI may assist with exploration, alternatives, scaffolding, summarization, critique, and draft implementations in these areas, but final adjudication remains with the human.
- When the agent provides a recommendation in a human-owned area, it must make clear that the human remains the final arbiter.

## 1.4) Research Document Standards (Mandatory)

- Treat research artifacts according to their purpose rather than forcing one uniform review style across all of them.
- Document-purpose standards:
  - `literature review` / `lit review`: source-backed synthesis only. Claims should be supportable from cited material and should avoid undocumented generalization.
  - `notes`: interpretation, extrapolation, hypotheses, implementation assumptions, and research-planning commentary are allowed, but they must be framed as such.
  - `notebooks`: prototype-specific empirical commentary is allowed when tied to the actual code, configuration, and observed outputs in that notebook.
- Do not force notebooks, notes, and lit reviews to sound the same. Require each to stay appropriate to its purpose instead.

## 1.5) Citation Verification Standards (Mandatory)

- For literature reviews and source-backed notebook/commentary claims, verify against the original article whenever the full text is available locally or has been obtained for review.
- When a cited paper exists in a local `research/.../sources` directory, prefer that local copy over web summaries for verification and page references.
- Add page numbers to in-text citations once the claim has been verified against the full text.
- If full text is not yet available, do not present the claim as fully verified. Mark the citation or section as pending full-text review.
- If a DOI resolves to a different article than the written citation, treat that as a hard citation error and correct the bibliography and in-text references together.
- Do not silently broaden narrow source support into broad system-level claims. If a broader statement is an inference, frame it explicitly as synthesis or interpretation.

## 1.6) Research Review Workflow (Mandatory)

- For requests to "review" research documents, default to findings-first read-only review unless the user explicitly asks for edits.
- In multi-step review chains (for example, "review X, then review Y"), do not edit a later document unless the user explicitly asks to implement changes there.
- For research citation audits, use this escalation order:
  - verify citation metadata,
  - verify full text if available,
  - add page numbers for verified claims,
  - classify unsupported wording as overclaim, inference, or unresolved,
  - only then propose or implement edits.
- When reviewing related research artifacts, check cross-document consistency across lit reviews, notes, notebooks, and bibliographies while respecting each document's purpose.
- Use a review-status note in literature reviews when some references remain pending full-text verification or when citation metadata has been corrected but interpretive details remain provisional.
- If a source is marked provisional in a literature review, related notes and notebooks should carry the same provisional status unless there is a clearly stated reason for different treatment.
- If the research review process itself materially changes, update `research/research-methodology.md` in the same change as the first affected research document.

## 1.7) Research Folder Conventions (Mandatory)

- Shared research-process documents belong at the top of the `research/` directory, not inside a topic folder.
- Topic-specific research materials belong inside a topic folder under `research/`.
- Use lowercase hyphenated names for research folders and research files by default.
- The standard topic-folder structure is:
  - `README.md`
  - `literature-review.md`
  - `research-notes.md`
  - optional `research-notebook.ipynb`
  - optional `sources/`
- Topic-document titles should align with the topic/folder name closely enough to read consistently as a set while still being understandable as standalone documents.
- Use `sources/` for local copies of research papers, manuals, reports, and other reference materials associated with a topic.
- Contents of topic-level `sources/` directories are local reference material and should not be committed unless the user explicitly directs otherwise.
- Not every topic folder must contain a notebook; include `research-notebook.ipynb` only when there is an actual prototype, experiment trail, or diagnostic artifact to document.
- Topic notebooks should be treated as prototype/experiment artifacts, not as canonical research summaries. Topic `README.md`, `literature-review.md`, and `research-notes.md` remain the primary orientation documents.
- `README.md` in each topic folder should provide:
  - a short topic overview,
  - links to the topic's main research files,
  - brief file descriptions,
  - and a short maturity note if that topic is still early-stage or has not yet undergone the same full review/refinement pass as other topics.
- Topic `README.md` files should remain orientation/index documents and should not expand into mini literature reviews.
- `research/README.md` should act as the shared research index and should link to topic `README.md` files rather than bare folders or individual topic artifacts.
- When one research topic depends materially on another, the dependent topic `README.md` should note that relationship explicitly.
- Prefer relative documentation links wherever possible, especially in shared indexes and repo-level documentation. Use absolute local paths only when there is a specific workflow reason to do so.
- When a topic folder is added, renamed, or materially restructured, update `research/README.md`, the topic `README.md`, and any affected root `README.md` references in the same change.
- When restructuring research folders, preserve consistency across:
  - the root `README.md`,
  - `research/README.md`,
  - topic-folder `README.md` files,
  - and cross-links between related research topics.

## 2) Explicit-Instruction-Only Mode (Mandatory)

- Do not edit, create, rename, or delete any file unless the user explicitly asks for that action.
- Do not run any shell/system command unless the user explicitly asks for that command or explicitly asks you to perform an action that clearly requires commands.
- Do not infer permission from context, prior turns, or "best next step".
- Treat proposal-style language, question-form phrasing, and declarative requirement statements as discussion by default, not execution permission, unless accompanied by a separate explicit execution cue.
- Require a separate explicit execution cue (for example: "implement this", "go ahead and make this change") before making changes after proposal/question discussion.
- Before executing any change after proposal/question discussion, send a preflight confirmation message: "Execution confirmation required. No changes made yet."
- After an explicit execution cue is received, execute without requesting another confirmation unless requirements changed materially or became ambiguous.
- If a message is ambiguous, mixes discussion with an implied task, or otherwise leaves intent unclear, ask a short clarifying question before taking any action.
- Default behavior is read-only discussion and planning until explicit user direction is given.
- For question-form prompts that ask for a review of one document and then mention another related artifact, treat the additional artifact as review-only unless a separate explicit execution cue is given for edits there.
- Explicit execution permission is non-overridable.
- An override may relax other eligible policy constraints for a specific operation, but it may not remove the requirement for explicit human authorization to execute the action itself.
- Permission to execute a change does not, by itself, mean the human has accepted the change as correct, validated, final, or authoritative.

## 3) Safety and Transparency

- Before any change, state exactly what you will do.
- For bug/failure remediation (for example CI/workflow errors), first explain the proposed fix and ask for explicit confirmation before making file edits.
- When changing GitHub Actions/workflow behavior, verify `AGENTS.md` policy text matches the realized workflow triggers and rules; if not aligned, update `AGENTS.md` in the same change.
- `uv.lock` is intentionally developer-local and not tracked in git for this repository. Do not commit it.
- Guardrails may be bypassed only after explicit user verification. This verification must be a separate interaction beyond the original action request, where the user explicitly confirms the bypass.
- Any bypass confirmation request must include a brief overview of the specific guardrail(s) being bypassed.
- After any change, summarize exactly what changed and where.
- If requested action conflicts with these rules, ask for confirmation and explain the conflict.

## 3.1) Override Governance (Mandatory)

- Override-governance rules are non-overridable.
- A valid override may bypass eligible policy rules only for one explicitly declared operation.
- An override must not be used to override, supersede, or recursively modify the override-governance rules.
- If an active override needs to change mid-stream, it must be amended as the same case rather than layered with a second override.
- An override exists only for the duration of the specific operation it was declared to support.
- Once that operation is complete, the override immediately ceases to be in effect.
- Any protection, safeguard, workflow control, or policy-dependent state bypassed under the override must be restored in full as part of completing the operation.
- An override is not complete until the supported operation has finished and all bypassed protections have been reinstated.
- If restoration cannot be completed immediately, that condition must be surfaced explicitly and treated as an unresolved exception requiring deliberate follow-up.
- Material overrides must be recorded in `.governance/policy-overrides.yaml`.
- Override records must follow `.governance/policy-overrides-spec.yaml`.
- Governance-process guidance for these files belongs in `.governance/README.md`.
- After an override is resolved, the agent must check whether it appears materially similar to prior recorded overrides.
- If the override appears to be part of a pattern, the agent must surface that to the developer and indicate that policy review should be considered.

## 3.2) Research Framing and Uncertainty Provenance (Mandatory)

- In notes documents, make clear whether a statement is:
  - source-backed summary,
  - inference,
  - hypothesis,
  - implementation assumption,
  - recommendation,
  - or future test/validation work.
- Use modality markers when needed to preserve that distinction, such as `suggests`, `appears`, `is expected to`, `hypothesis`, `to be tested`, or `in this pipeline design`.
- In notebooks, concrete prototype-specific findings are allowed, but do not claim downstream validity from local reconstruction diagnostics unless the notebook actually evaluates the downstream task.
- Distinguish uncertainty provenance explicitly:
  - published QC/error specifications,
  - uncertainty fields present in the working dataset,
  - implementation-specific approximations or summaries,
  - empirically validated calibration or coverage behavior.
- Do not present a custom uncertainty model as though it were directly specified by a cited source unless the implementation actually follows that source at that level.
- When uncertainty language mixes source-derived conventions with local implementation choices, name both pieces explicitly so readers can tell what is authoritative versus local approximation.

## 3.3) Review Request Routing (Mandatory)

- If the user asks for a `review`, determine whether the target is code or research material before applying a review standard.
- For code review requests, prioritize bugs, regressions, behavioral risks, and missing tests.
- For research/document review requests, prioritize citation accuracy, claim calibration, source alignment, and cross-document consistency.
