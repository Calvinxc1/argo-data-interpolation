# Operational Framing Notes: Underwater Acoustics

These working notes capture the broader underwater-acoustics framing for uncertainty-aware Argo profile interpolation. This document is intentionally broader and more proposal-oriented than the topic literature review. Source-backed claims currently trace only to [../literature-review.md](../literature-review.md). Candidate ecosystem, tooling, and market claims are kept here as pending verification targets rather than established support.

## Source-backed anchor

The verified starting point for this topic is narrow but useful: Jana et al. (2022) shows that Argo-derived sound-speed profiles can be used to study variability, sonic layer depth, surface ducting, and shadow-zone-relevant structure in a real regional setting. This is covered in [Argo-Derived Sound Speed Climatologies and Regional Variability](../literature-review.md#argo-derived-sound-speed-climatologies-and-regional-variability). That section, together with [Acoustic Applications Increasingly Depend on Argo](../literature-review.md#acoustic-applications-increasingly-depend-on-argo), is enough to justify underwater acoustics as a legitimate downstream application area for the present package.

## Hypothesis

The strongest industry-facing wedge for this project is not "better interpolation" in the abstract. It is:

**uncertainty-aware sound-speed profile generation from Argo data for acoustics-sensitive workflows**

That framing keeps the package at the environmental-input layer, where it is differentiated, while avoiding the much broader claim that it solves underwater acoustics end to end.

## Underwater Intervention 2026 framing

The current conference target is Underwater Intervention 2026, scheduled for December 2-4, 2026 at the Morial Convention Center in New Orleans. The Call for Speakers closes on April 30, 2026. For this submission, the preferred track is Emerging Technologies & Innovation rather than Uncrewed Maritime Systems. That track choice is a local proposal decision, but it is grounded in the published track descriptions: Uncrewed Maritime Systems is framed mainly around seafloor data collection, mapping, and survey techniques, while Emerging Technologies & Innovation explicitly emphasizes AUVs, real-time oceanographic data, underwater communications, and other enabling technologies for future operations.

The talk scope should stay deliberately bounded. The concrete work being presented is Jason's replication of Jana et al. (2022) plus a normal-distribution-based uncertainty layer attached with his own library, with that uncertainty-aware path compared back to the deterministic baseline rather than presented as an untested add-on. The abstract should not promise the MRST-PCHIP Python implementation as required deliverable scope. If that path matures in time, it can appear as a bonus comparison or discussion point rather than as the central commitment.

## Operational translation

The current source-backed anchor from the literature review is narrower: Argo-informed temperature-salinity and sound-speed-relevant ocean fields are upstream inputs to operationally relevant acoustic environments. The more specific HYCOM/NCODA and Navy-workflow translation is still a notes-level interpretation rather than a canonical literature-review claim. The clean operator-facing translation is therefore not "here is a nicer interpolation method." It is: when someone substitutes a model-derived or Argo-informed profile for a local cast, they are accepting a risk whose size is usually hidden.

That is the core "so what" for the conference audience. If floats are sparse, peripheral to the cell, or temporally stale relative to the requested profile, the operator currently gets a point estimate with little signal that the estimate is weakly constrained. The package contribution is to quantify that constraint quality at the source and convert it into a practical decision question: is the prior good enough to proceed, or does this job warrant an in-situ cast?

The open-access 2025 *Satellite Navigation* paper on GNSS-acoustic seafloor positioning is currently the strongest candidate industry-facing example for this audience. A local PDF copy is now stored under `sources/` as `liu-2025-precise_gnss_acoustic_seafloor_positioning_global_ocean_analysis.pdf`. Because this source has not yet been promoted into the canonical literature review, its HYCOM-for-GNSS-A result should be treated here as a pending extension hook rather than as established support.

## Visualization and title

The current best demo concept is simple and legible: keep color for the interpolated value, and use saturation to encode certainty. In the Jana-style 2 degree by 2 degree box, a cell with floats clustered on the periphery should leave the center washed out, making the interpolation's weakness visually obvious without requiring the audience to parse covariance language.

Current title candidate: **How Good Is That Argo Profile, Really? Confidence in the Space Between Floats.**

## Open question

One unresolved technical question to keep visible is mesoscale structure. Eddies and fronts could produce situations where a grid-box center appears well constrained numerically even though the floats mainly sampled the edges of a mesoscale feature rather than its interior. That failure mode needs explicit checking before the visualization is treated as a general confidence map.

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

- underwater acoustic communications planning
- marine environmental acoustics and regulatory impact assessment
- which public acoustic propagation codes or wrappers are the best reproducible fit for downstream uncertainty demonstrations

### Operational-domain claims now partly anchored

- sonar performance prediction and ASW transmission-loss workflows now have a source-backed anchor through the HYCOM/NCODA and Navy operational references already promoted into [../literature-review.md](../literature-review.md)
- AUV or USV acoustic positioning now has a concrete candidate source in the 2025 *Satellite Navigation* HYCOM/GNSS-A paper, with a local PDF now available for promotion into the canonical review

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
