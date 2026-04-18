# Error Propagation Architecture Notes

This note captures the current error taxonomy for the underwater-acoustics interpolation and uncertainty workflow associated with the IEEE Oceans 2026 paper path.

## Active Error Terms

### 1. Spatiotemporal interpolation error

This is the structural uncertainty of the kernel-based held-out interpolation itself. It reflects unresolved spatial gradients, temporal variability, kernel representativeness limits, and other mismatch between the target cycle and its neighboring cycles.

Current status:
- Actively addressed in the package.
- Estimated from held-out interpolation residuals using point-estimate neighboring observations.
- Intentionally defined without observation-uncertainty inputs, so it remains a structural interpolation term rather than a measurement-quality term.

### 2. Observation error propagated through kernel weights

Each observation entering the spatiotemporal kernel carries its own uncertainty from the upstream cycle-interpolation model error and sensor error, including direct and pressure-propagated components. Because the kernel is linear, this propagates through the weighted combination as:

`sum_i w_i^2 * sigma_i^2`

Current status:
- Actively addressed in the package.
- Treated as additive with the spatiotemporal interpolation term.
- Considered independent of the spatiotemporal interpolation error because the held-out interpolation error was computed from point estimates and is therefore blind to observation uncertainty.

### 3. Kernel parameter uncertainty

The kernel parameters themselves, such as length scales and bandwidth terms, are estimated from data and therefore carry estimation noise. That uncertainty propagates into the interpolation through the induced uncertainty on the kernel weights, naturally framed through a delta-method treatment.

Current status:
- Actively addressed in the package architecture.
- Expected to be secondary when parameter estimates are well constrained on dense datasets.
- Still worth acknowledging explicitly because it is a distinct source of additive uncertainty.

## Acknowledged but Not Active Error Terms

### 4. Surface GPS and timestamp error

This is the positioning and timing uncertainty attached to the reported surface fix used for cycle localization.

Current status:
- Acknowledged explicitly.
- Judged negligible for the present work relative to the spatial and temporal scales used by the kernel.
- Not modeled as a separate propagated term in the current package.

### 5. Float drift during ascent and descent

This is the mismatch between the surface capture point and the actual in-water path of the float while it ascends and descends. It affects the effective spatial and temporal inputs seen by the kernel even if the reported surface fix is accurate.

Current status:
- Acknowledged explicitly.
- Flagged as deferred for future work.
- Relevant to kernel-input fidelity, but not yet carried as an active uncertainty term in the current implementation.

## Working Summary

The current package architecture treats uncertainty as the sum of three main terms:

1. Spatiotemporal interpolation error.
2. Observation error propagated through kernel weights.
3. Kernel parameter uncertainty.

GPS and timestamp error are currently treated as negligible. Float-drift positioning error is recognized as real but deferred.
