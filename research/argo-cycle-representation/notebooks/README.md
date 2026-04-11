# Argo Cycle Representation Notebooks

This folder contains prototype and experiment notebooks for the `argo-cycle-representation` topic. These notebooks are implementation and diagnostic artifacts, not canonical source-backed summaries. Source-backed claims made in notebook commentary should trace to sources already covered in [../literature-review.md](../literature-review.md).

Committed notebooks in this folder are paired with Jupytext `.py` files in percent format. The `.ipynb` remains the primary runnable research artifact; the paired `.py` file exists to make notebook content easier to diff, review, and search in version control.

## Files

- [01-cycle-representation-baseline.ipynb](01-cycle-representation-baseline.ipynb) and [01-cycle-representation-baseline.py](01-cycle-representation-baseline.py): baseline prototype notebook for the current spline workflow, uncertainty construction, reconstruction diagnostics, and next-step experiment framing.
- [02-cycle-representation-validation.ipynb](02-cycle-representation-validation.ipynb) and [02-cycle-representation-validation.py](02-cycle-representation-validation.py): comparative validation notebook for omitted-point RMSE, artifact memory footprint, serialized size, and footprint stability against Akima and PCHIP baselines.
- [03-cycle-representation-comparisons.ipynb](03-cycle-representation-comparisons.ipynb) and [03-cycle-representation-comparisons.py](03-cycle-representation-comparisons.py): exploratory comparison notebook for linear, PCHIP, and native SciPy spline-family models, used to narrow the research direction toward compact uncertainty-aware representations.
- [lib/](lib/): research-only notebook support modules used to keep the notebooks readable and reproducible without promoting experimental code into `src/`.

## License

This folder is part of the [`research/`](../../README.md) subtree and is
licensed under the Creative Commons Attribution 4.0 International
license unless otherwise noted. See [`../../LICENSE`](../../LICENSE).
The non-research parts of the repository remain under the GNU General
Public License v3.0 or later as described in
[`../../../README.md`](../../../README.md).
