# Jana Replication Notes: Underwater Acoustics

These working notes capture how the Jana et al. study can be used as the current downstream demonstration target for uncertainty-aware Argo profile interpolation. Source-backed claims in this file trace to [../literature-review.md](../literature-review.md). Broader downstream-model or package-specific statements that are not yet in the literature review are marked as proposal-level recommendations or future validation work.

## Source-backed summary

Jana et al. (2022) is currently the cleanest verified anchor for this topic because it uses public Argo observations, converts temperature and salinity to sound speed, interpolates the resulting profiles to a uniform 1 m grid from 5 m to 500 m, and analyzes outputs that matter acoustically, including sound-speed variability structure and sonic-layer-related interpretation.

The paper's retained dataset size, filtering rules, and deterministic profile-processing sequence make it suitable for a like-for-like replication baseline. The strongest verified reason to use it is not that it is the most sophisticated acoustic study, but that it exposes a narrow, reproducible Argo-to-sound-speed workflow where interpolation choices are visible and downstream interpretation remains understandable.

## Inference

This study is a better initial showcase than a full uncertainty-aware acoustic-propagation paper because it isolates the exact stage where the current package aims to contribute. The project does not need to invent a new acoustic solver to demonstrate value. It can first show that the interpolation step itself can emit a sound-speed profile with explicit uncertainty structure instead of a silent point estimate.

The most defensible extension path is:

1. Reproduce the Jana baseline outputs as closely as practical.
2. Replace the deterministic profile gridding step with PCHIP and/or smoothing-spline variants that emit per-level uncertainty estimates.
3. Quantify how those uncertainty estimates affect derived sound-speed structure, sonic layer depth identification, and any downstream acoustic diagnostic added in the extension study.

## Recommendation

The replication should keep one strong baseline path that stays as close as possible to Jana et al., including the original sound-speed equation if needed for a strict comparison. A second path can then introduce the TEOS-10/GSW sound-speed calculation as an explicit upgrade so interpolation effects and equation-of-state effects are not conflated in the first comparison.

The current project story is strongest if it shows two things separately:

- changing the interpolation method changes the gridded sound-speed structure in physically meaningful regions such as sharp gradients and sonic-layer-relevant depths
- attaching uncertainty at the interpolation stage gives the downstream acoustic workflow information it did not previously have

## Implementation assumption

The likely first downstream acoustic extension is a simple deterministic propagation workflow run repeatedly over an ensemble of uncertainty-aware sound-speed profiles rather than a bespoke stochastic acoustic solver. That choice is an implementation strategy for the package demonstration, not yet a source-backed claim for this topic.

## Future validation work

- Verify primary-source details for the acoustic model or wrapper selected for the downstream extension.
- Determine whether the Jana workflow's exact interpolation method can be confirmed from paper text, supplementary material, or reproducible code.
- Add source-backed coverage for any acoustic-metric sensitivity claims before using them in canonical writing.
