# Operational Framing Notes: Underwater Acoustics

These working notes capture the broader underwater-acoustics framing for uncertainty-aware Argo profile interpolation. This document is intentionally broader and more proposal-oriented than the topic literature review. Source-backed claims currently trace only to [../literature-review.md](../literature-review.md). Candidate ecosystem, tooling, and market claims are kept here as pending verification targets rather than established support.

## Source-backed anchor

The verified starting point for this topic is narrow but useful: Jana et al. (2022) shows that Argo-derived sound-speed profiles can be used to study variability, sonic layer depth, surface ducting, and shadow-zone-relevant structure in a real regional setting. This is covered in [Argo-Derived Sound Speed Climatologies and Regional Variability](../literature-review.md#argo-derived-sound-speed-climatologies-and-regional-variability). That section, together with [Acoustic Applications Increasingly Depend on Argo](../literature-review.md#acoustic-applications-increasingly-depend-on-argo), is enough to justify underwater acoustics as a legitimate downstream application area for the present package.

## Hypothesis

The strongest industry-facing wedge for this project is not "better interpolation" in the abstract. It is:

**uncertainty-aware sound-speed profile generation from Argo data for acoustics-sensitive workflows**

That framing keeps the package at the environmental-input layer, where it is differentiated, while avoiding the much broader claim that it solves underwater acoustics end to end.

## Candidate claims pending source verification

The current research dump surfaced several ecosystem-level claims that appear promising but still need primary-source verification before they move into the literature review.

### Toolchain-gap claims to verify

- whether common Argo Python access tools expose only deterministic vertical interpolation in their standard profile-gridding utilities
- whether common Python interfaces to acoustic propagation codes accept only deterministic sound-speed profiles and therefore require manual Monte Carlo orchestration for uncertainty studies
- which acoustic codes or wrappers are the best public, reproducible fit for a package demonstration

### Uncertainty-budget claims to verify

- how much of the total acoustic uncertainty budget can be attributed to Argo sensor-error fields versus representativeness error, vertical interpolation error, and temporal aliasing
- which uncertainty components can be attached honestly at the profile-interpolation stage and which require broader spatiotemporal modeling assumptions
- what uncertainty representation is most useful downstream: per-depth intervals, covariance matrices, or ensemble realizations

### Operational-domain claims to verify

- sonar performance prediction
- AUV or glider navigation and acoustic positioning
- multibeam survey support and total-propagated-uncertainty workflows
- underwater acoustic communications planning
- marine environmental acoustics and regulatory impact assessment

The current working expectation is that at least one of these domains will provide a stronger industry-facing demonstration than a purely oceanographic interpolation benchmark, but that expectation still needs to be backed by reviewed sources.

## Recommendation

Keep the downstream demonstration story tightly scoped:

1. Argo profile in.
2. Uncertainty-aware sound-speed profile out.
3. Existing deterministic acoustic workflow consumes an ensemble or interval-aware representation.
4. Resulting acoustic spread is summarized in a form an operational audience can understand.

This keeps the package's contribution narrow, legible, and defensible.

## Future validation work

- Add primary-source coverage for acoustic propagation toolchains and their input constraints.
- Add source-backed operational examples with quantified consequences of sound-speed uncertainty.
- Distinguish clearly between uncertainty that comes from published data conventions and uncertainty that comes from local modeling choices.
