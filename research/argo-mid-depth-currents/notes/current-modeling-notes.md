# Current Prediction Notes

Working notes on the problem of predicting ocean currents from Argo float data and on why the simplest trajectory-based idea was parked.

---

## Source-backed summary

The seed literature for this topic points to a clear reference chain:

- the Scripps Argo trajectory-based velocity product is the modern benchmark dataset for parking-depth currents
- parking-depth velocity errors have already been decomposed in the literature rather than needing to be invented locally
- the official Argo timing model distinguishes ascent end from the subsequent surface-location sequence, so a single reported GIS position should not be assumed to be the exact location of the ascent profile or drift endpoint
- thermal-wind plus a parking-depth reference velocity is the standard physical path from mid-depth velocity to a vertically resolved absolute flow estimate
- trajectory assimilation is the more operationally mature direction when current information needs to influence an ocean state estimate

These source-backed points are summarized in [../literature-review.md](../literature-review.md).

## Inference

The original movement-profile idea is too weak if it assumes that parking-depth displacement is an adequate stand-in for the full vertical flow structure. It is also too weak if it silently treats the profile-level GIS coordinate as the exact horizontal location of measurements collected during ascent. That is especially hard to defend in a basin with strong stratification, seasonal forcing, boundary effects, and eddy activity.

## Hypothesis

Distinct trajectory groupings may still be picking up physically distinct advective regimes rather than only noise. That observation is still useful, but it should be treated as a hypothesis-generator rather than as evidence that a bespoke trajectory-weighted predictor is already justified.

## Recommendation

Do not build a custom movement-profile predictor as the next step.

If Argo-based current prediction becomes a real workstream, the defensible entry path is:

1. start from the Scripps parking-depth velocity product
2. treat ascent-end and surface-fix positions as a trajectory-estimation problem rather than as a raw GIS field lookup
3. reference thermal-wind shear to that absolute mid-depth velocity
4. test the resulting vertically resolved flow field as a separate modeling product with its own diagnostics and error analysis

That is large enough to be its own paper-scale effort.

## Future validation work

- Acquire and verify the Weddell Gyre and Mediterranean trajectory-assimilation papers identified in the tracker.
- Decide whether Bay of Bengal latitude and boundary-current structure make thermal-wind diagnostics too fragile for this use case.
- Check whether existing Indian Ocean / NASCar tooling already supplies enough infrastructure to revisit this later without building a custom flow product from scratch.
