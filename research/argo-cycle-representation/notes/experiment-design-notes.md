# Experiment Design Notes: Argo Cycle Representation

These notes capture implementation options and the remaining experiments that still matter after notebooks 01-03. Source-backed method references should trace to [../literature-review.md](../literature-review.md). Package names, implementation mappings, and experiment priorities below are local engineering notes rather than literature-backed claims unless stated otherwise.

## What is already established in the notebooks

The notebook sequence has already answered several earlier experiment questions:

- notebook 01 established that the custom curvature-adaptive spline is a real working prototype,
- notebook 02 compared that prototype against Akima and PCHIP on withheld-point RMSE, artifact footprint, and footprint stability,
- notebook 03 compared the broader spline direction against linear and PCHIP using native SciPy spline-family implementations and made the case that the custom method may not be worth carrying forward.

So this note should no longer be read as a blank pre-results plan. It is now a roadmap for the experiments that remain useful after those comparisons.

## Practical implementation mappings

### Akima

`scipy.interpolate.Akima1DInterpolator` remains the recommended engineering implementation for Akima-style comparison work. It is built into SciPy and is sufficient for the exact-interpolant baseline role already used in notebook 02.

```python
from scipy.interpolate import Akima1DInterpolator

akima = Akima1DInterpolator(pres, temp)
temp_interp = akima(query_pressures)
```

SciPy also exposes a modified variant (`method="makima"` added in SciPy 1.13.0) that may be worth testing if a smoother local exact-interpolant baseline is still desired.

### PCHIP

`scipy.interpolate.PchipInterpolator` remains the practical shape-preserving exact-interpolant baseline for this project.

```python
from scipy.interpolate import PchipInterpolator

pchip = PchipInterpolator(pres, temp)
temp_interp = pchip(query_pressures)
```

This is still a proxy for the broader PCHIP family rather than a full MRST-PCHIP implementation, but it is adequate for the role the notebooks currently ask it to play.

### Native spline path

The active spline comparison path is now the native SciPy/FITPACK route through `make_splrep` or the project wrapper that exposes the same family through `SplineAdapter`. That is the spline branch that now deserves most future experiment time.

## Remaining high-value experiments

### Experiment 1: smoothing frontier for the native spline family

Notebook 03 established that the spline family remains interesting because `s` gives a direct handle on fidelity versus footprint. The next obvious experiment is to map that frontier more systematically.

For each cycle or cycle sample:

- sweep a range of `s` values,
- record withheld-point RMSE,
- record memory and serialized footprint,
- inspect how the uncertainty fields should change as smoothing increases.

The goal is not to find a single global best `s`. The goal is to characterize the tradeoff surface the project is now actually interested in.

### Experiment 2: transfer of the notebook 01 uncertainty model

Notebook 01 built an interpretable uncertainty decomposition around the custom spline artifact. Notebook 03 makes it necessary to ask which parts of that decomposition should survive when the underlying spline implementation changes.

Questions to test:

- Does the same residual-plus-sensor-plus-gradient construction still make sense for native spline artifacts?
- Does the approximation term scale sensibly as `s` increases?
- Can uncertainty widening reflect lower fidelity rather than masking it?

This is now more valuable than further custom-knot tuning.

### Experiment 3: robustness tests on the surviving contenders

The old custom method motivated noise and spike robustness arguments. Those arguments should not be discarded, but the target set has changed.

The useful robustness comparison is now:

- PCHIP,
- native spline with `s = 0` or near-zero,
- native spline with positive smoothing,
- optionally the historical custom spline if preserving the negative-result story needs a reproducible robustness comparison.

#### Noise injection

Inject Gaussian noise at the sensor-spec level and compare RMSE degradation.

```python
np.random.seed(42)
noise = np.random.normal(0, 0.002, size=len(temp))
temp_noisy = temp + noise
```

#### Spike injection

Inject an isolated spike in a thermocline region and compare how much distortion propagates into neighboring depths.

```python
temp_spiked = temp.copy()
spike_idx = np.argmin(np.abs(pres - 150))
temp_spiked[spike_idx] += 0.5
```

The point of these tests is no longer to rescue the custom method. It is to decide whether the retained spline-family direction has a robustness story worth keeping.

### Experiment 4: reproducible negative-result appendix

If the curvature-adaptive prototype remains in the topic as a negative result, the remaining experimental task is not general optimization. It is reproducible characterization.

Useful outputs:

- overlay knot locations on representative success and failure cases,
- sensitivity to smoothing-window and peak-detection settings,
- holdout RMSE relative to native spline and PCHIP,
- artifact size and knot-count summaries,
- a small set of "works / degrades / fails badly" examples.

That would preserve the branch honestly without keeping it as the project's live optimization target.

## Lower-priority or optional experiments

### Reiniger-Ross

There is still no strong reason to prioritize Reiniger-Ross unless a historical oceanographic comparator is specifically needed for a paper or appendix. The current stack does not expose it cleanly.

### Full MRST-PCHIP

Implementing full MRST-PCHIP could still be worthwhile if the project later needs a stronger exact-interpolant comparator tied more directly to Barker and McDougall (2020). In the current Python stack, that is not an off-the-shelf package switch: the official GSW-Python docs expose MRST only inside the geostrophic-height routines, not as a standalone profile-interpolation API. A true comparator would therefore require either wrapping the relevant GSW C path or reimplementing the published method directly. It is not the highest-priority next experiment for the current research direction, which is now centered more on native spline tradeoffs and uncertainty.

## Current experimental priority order

1. native spline `s` frontier mapping,
2. uncertainty-transfer and calibration experiments,
3. robustness tests on PCHIP versus native spline variants,
4. reproducible negative-result appendix for the custom spline,
5. optional stronger exact-interpolant baselines if a later write-up requires them.
