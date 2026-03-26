# Experiment Design Notes: Argo Cycle Representation

These notes capture implementation options and planned validation experiments for the current cycle-representation pipeline. Source-backed method references should trace to [../literature-review.md](../literature-review.md).

## Python implementations for comparison experiments

### Akima

`scipy.interpolate.Akima1DInterpolator` is the recommended implementation. It is built into SciPy with no additional installation required and is the same algorithm referenced in the oceanographic literature.

```python
from scipy.interpolate import Akima1DInterpolator

akima = Akima1DInterpolator(pres, temp)
temp_interp = akima(query_pressures)
```

SciPy also exposes a modified variant (`method="makima"` added in SciPy 1.13.0) that further reduces overshoot by modifying the weight computation. Worth including in the comparison for completeness.

### Reiniger-Ross

There is no dedicated Python implementation of Reiniger-Ross. The canonical implementation is in the R `oce` package as `oceApprox(method="reiniger-ross")`, callable from Python via `rpy2`. The GSW-MATLAB toolbox contains `gsw_rr68_interp_SA_CT`, callable from Python via `oct2py`.

For the comparison experiments, SciPy's `PchipInterpolator` and `Akima1DInterpolator` are probably sufficient without needing Reiniger-Ross, which is largely a historical baseline.

### MRST-PCHIP proxy

`scipy.interpolate.PchipInterpolator` is plain PCHIP without the 16-rotation MR enhancement. It is an exact interpolant forced through every observation, which is the critical property shared with MRST-PCHIP that matters for the noise and spike injection experiments.

```python
from scipy.interpolate import PchipInterpolator

pchip = PchipInterpolator(pres, temp)
temp_interp = pchip(query_pressures)
```

Full MRST-PCHIP can be implemented directly from Barker and McDougall (2020). The core is 16 PCHIP calls on rotated coordinate systems averaged back to the original frame, using observation index rather than pressure as the independent variable. Estimated implementation effort is a few hours. The `gsw` Python package does not currently expose the interpolation functions.

## Quantitative comparison experiments

### Experiment 1: noise injection test

Inject synthetic Gaussian noise at the Argo sensor-spec level (0.002 C standard deviation for temperature) into random pressure levels of a held-out cycle. Run both PCHIP and this pipeline on the noisy version and measure reconstruction error against the clean original at all other pressure levels. The key metric is how much each method's RMSE degrades under noise.

```python
np.random.seed(42)
noise = np.random.normal(0, 0.002, size=len(temp))
temp_noisy = temp + noise

degradation_pchip = rmse_pchip_noisy - rmse_pchip_clean
degradation_spline = rmse_spline_noisy - rmse_spline_clean
```

### Experiment 2: spike injection test

Inject a single large spike (0.5 C) at one pressure level in the thermocline. Measure how far the artifact propagates into adjacent depths in each method. PCHIP must honor the spike and the distortion bleeds into neighboring intervals. This pipeline should absorb it as a local residual without propagating it.

```python
temp_spiked = temp.copy()
spike_idx = np.argmin(np.abs(pres - 150))
temp_spiked[spike_idx] += 0.5

adjacent_mask = (np.abs(pres - pres[spike_idx]) > 0) & \
                (np.abs(pres - pres[spike_idx]) <= 20)

propagation_pchip = rmse(pchip(pres[adjacent_mask]), temp[adjacent_mask])
propagation_spline = rmse(spline(pres[adjacent_mask]), temp[adjacent_mask])
```

### Experiment 3: cross-validation holdout RMSE comparison

Extend the existing 5-fold cross-validation to also run PCHIP on the same holdout folds. This produces a true apples-to-apples RMSE comparison on the same data using the same validation framework. This is the most publishable comparison because it reports a per-profile RMSE benchmark that does not exist anywhere in the published literature.

```python
from scipy.interpolate import PchipInterpolator

for fold in range(5):
    train_idx, test_idx = fold_indices[fold]

    pchip = PchipInterpolator(pres[train_idx], temp[train_idx])
    rmse_pchip_fold = rmse(pchip(pres[test_idx]), temp[test_idx])

    spline = fit_spline(pres_uniform, temp_smooth_uniform, knots)
    rmse_spline_fold = rmse(spline(pres[test_idx]), temp[test_idx])
```

### Experiment 4: serialized file-size comparison

Measure the serialized file sizes of each method's stored representation per cycle across all cycles in the current dataset.

```python
import pickle

pchip_storage = {"pres": pres, "temp": temp}
spline_storage = {
    "temp_t": temp_spline.t,
    "temp_c": temp_spline.c,
    "temp_k": temp_spline.k,
    "temp_rmse": cycle_rmse,
    "sal_t": sal_spline.t,
    "sal_c": sal_spline.c,
    "sal_k": sal_spline.k,
    "sal_rmse": sal_rmse,
}

def pickled_size(obj):
    return len(pickle.dumps(obj))

print(f"PCHIP storage: {pickled_size(pchip_storage)} bytes")
print(f"This pipeline: {pickled_size(spline_storage)} bytes")
print(
    f"Compression ratio: "
    f"{pickled_size(pchip_storage) / pickled_size(spline_storage):.1f}x"
)
```

Run this across all cycles and report mean, median, and range of compression ratios.
