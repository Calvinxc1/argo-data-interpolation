# Curvature-Adaptive Spline Negative Result

These notes preserve the research story around the curvature-adaptive least-squares spline prototype. This file is a project-facing interpretation and experiment-design note, not a source-backed literature summary. Source-backed claims about adaptive spline methods belong in [../literature-review.md](../literature-review.md) and [adaptive-spline-analogues.md](adaptive-spline-analogues.md).

## Summary

The curvature-adaptive LSQ spline was a plausible first design for compact Argo cycle representation, but it should be treated as a negative result rather than the current core method.

The original idea was:

1. smooth each profile enough to separate large-scale structure from local noise,
2. estimate curvature or second-derivative structure,
3. place spline knots where the profile bends most strongly,
4. fit a compact least-squares spline that is not forced through every observation,
5. store the resulting spline coefficients as a small queryable artifact.

That story remains useful because it explains the method-development path. It should not be presented as a validated advantage unless the validation notebook demonstrates that it works.

## Why the idea was plausible

The physical intuition was reasonable. Argo profiles often concentrate their most important vertical structure in thermoclines, haloclines, mixed-layer transitions, and other relatively narrow pressure bands. A compact model should ideally spend degrees of freedom in those regions and avoid wasting parameters in broad, nearly linear or weak-gradient regions.

The statistical intuition was also reasonable. Exact interpolants such as linear interpolation and PCHIP honor every retained observation. That is useful when observations are treated as the target curve, but it can propagate sensor noise, unresolved small-scale variability, or isolated spikes into the interpolated profile. A least-squares representation that is not forced through every point could, in principle, recover the profile-scale structure while averaging down local noise.

The implementation intuition was therefore:

- curvature should identify where knots matter,
- smoothing before curvature estimation should prevent noise from driving knot placement,
- LSQ fitting should reduce sensitivity to individual observations,
- the final artifact should be smaller than methods that retain the full observed profile.

## What went wrong

The failure mode is that curvature-adaptive knot placement is itself a difficult inference problem. The signal used to allocate knots is noisy, sparse, and sensitive to preprocessing choices.

Observed or expected weaknesses to demonstrate in the validation notebook:

- Curvature estimates are unstable unless the profile is smoothed heavily.
- Heavy smoothing can erase the same sharp structure the knot detector is supposed to preserve.
- Peak-detection parameters can dominate the resulting knot layout.
- Weak, broad, double, or noisy thermocline structure can produce brittle knot choices.
- Boundary regions can behave poorly because curvature and residual signals are less well supported near profile ends.
- The LSQ fit can underfit sharp transitions when too few knots are selected.
- Added implementation complexity may not buy enough RMSE, robustness, or storage improvement to justify itself.

The important research lesson is not that adaptive knots are impossible. It is that a physically appealing knot-placement heuristic does not automatically become a robust profile representation method.

## How to present the negative result

The validation notebook should preserve this method as a historical prototype or negative-result comparison, not as the production spline path.

Suggested framing:

> We first tested a curvature-adaptive least-squares spline because it matched the physical intuition that Argo profile structure is concentrated in high-curvature vertical regions. Validation showed that the approach was too brittle and parameter-sensitive to serve as a robust default. We therefore retained the compact-representation question but shifted the main comparison toward simpler, better-defined methods: linear interpolation, PCHIP, and FITPACK smoothing splines through `scipy.interpolate.make_splrep`.

Useful notebook evidence:

- overlay knot locations on profile curves and curvature estimates,
- show examples where the method works, fails mildly, and fails badly,
- compare holdout RMSE against linear, PCHIP, and FITPACK smoothing splines,
- report knot count and serialized artifact size,
- test sensitivity to smoothing-window and peak-detection parameters,
- include spike-injection or noise-injection diagnostics if they reveal the intended robustness tradeoff.

## Relationship to FITPACK smoothing splines

`scipy.interpolate.make_splrep` with `s > 0` is still relevant, but it tells a different story. It creates a smoothing spline that is not forced through every point and can produce a compact `BSpline` representation. Its automatic knot placement is residual-driven through the FITPACK heuristic, not explicitly curvature-driven.

That distinction should be made clear:

- curvature-adaptive LSQ spline: historical prototype, custom knot-selection idea, negative-result candidate;
- FITPACK smoothing spline: current pragmatic spline baseline, controlled primarily through the smoothing parameter `s`;
- linear and PCHIP: exact-interpolant baselines.

## Recommended notebook role

With the current notebook sequence, the curvature-adaptive prototype now has a clearer place:

- notebook 01 preserves it as a serious working prototype and method-confirmation artifact,
- notebook 02 tests it against exact-interpolant baselines and establishes the actual tradeoff,
- notebook 03 is where the project decides that the broader spline direction survives more convincingly through simpler native spline-family methods.

That sequence is preferable to pretending the custom method never mattered. The point of the negative-result framing is not to erase the prototype; it is to show honestly that it was explored seriously and then set aside for a cleaner direction.
