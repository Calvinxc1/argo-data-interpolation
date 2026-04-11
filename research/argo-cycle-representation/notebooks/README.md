# Argo Cycle Representation Notebooks

This folder contains prototype and experiment notebooks for the `argo-cycle-representation` topic. These notebooks are implementation and diagnostic artifacts, not canonical source-backed summaries. Source-backed claims made in notebook commentary should trace to sources already covered in [../literature-review.md](../literature-review.md).

## Files

- [01-cycle-representation-baseline.ipynb](01-cycle-representation-baseline.ipynb): baseline prototype notebook for the current spline workflow, uncertainty construction, reconstruction diagnostics, and next-step experiment framing.
- [02-cycle-representation-validation.ipynb](02-cycle-representation-validation.ipynb): comparative validation notebook for omitted-point RMSE, artifact memory footprint, serialized size, and footprint stability against Akima and PCHIP baselines.
- [03-cycle-representation-comparisons.ipynb](03-cycle-representation-comparisons.ipynb): comparison notebook for the modern package API, including linear, PCHIP, and spline-family model builds on the current cycle interfaces.

## License

This folder is part of the [`research/`](../../README.md) subtree and is
licensed under the Creative Commons Attribution 4.0 International
license unless otherwise noted. See [`../../LICENSE`](../../LICENSE).
The non-research parts of the repository remain under the GNU General
Public License v3.0 or later as described in
[`../../../README.md`](../../../README.md).
