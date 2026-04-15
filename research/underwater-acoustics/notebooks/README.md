# Underwater Acoustics Notebooks

This folder indexes prototype notebooks for the `underwater-acoustics` topic. These notebooks are experiment artifacts, not canonical summaries. Source-backed claims should trace back through [../literature-review.md](../literature-review.md), with notebook-specific interpretations kept tied to the actual saved experiment state.

Committed notebooks in this folder are paired with Jupytext `.py` files in percent format. The `.ipynb` remains the primary runnable research artifact; the paired `.py` file exists to make notebook content easier to diff, review, and search in version control.

## Files

- [1-jana-study-replication.ipynb](1-jana-study-replication.ipynb) and [1-jana-study-replication.py](1-jana-study-replication.py): replication notebook for Jana et al. (2022), covering Argo data pull and filtering, profile interpolation, sound-speed calculation, and the figure-reproduction workflow through the current subdomain composites.
- [2-jana-holdout-validation.ipynb](2-jana-holdout-validation.ipynb) and [2-jana-holdout-validation.py](2-jana-holdout-validation.py): hold-one-float-out benchmark notebook that evaluates a Jana-style flat `2° x 2°` retained-cycle kernel predictor on the retained Bay of Bengal archive and aggregates profile error by depth.
- [3-uncertainty-extension.ipynb](3-uncertainty-extension.ipynb) and [3-uncertainty-extension.py](3-uncertainty-extension.py): weighted hold-one-float-out comparison notebook that uses the same retained archive and validation protocol as the Jana benchmark, but replaces the flat retained-cycle mean with a weighted retained-cycle predictor inside the same spatial kernel.
- [4-uncertainty-extension-all-cycles.ipynb](4-uncertainty-extension-all-cycles.ipynb) and [4-uncertainty-extension-all-cycles.py](4-uncertainty-extension-all-cycles.py): weighted hold-one-float-out comparison notebook that keeps the same local moving window as notebook `3`, but relaxes archive-retention rules so partially sampled cycles can contribute where they provide actual depth support, with explicit dropped-depth accounting.

## License

This folder is part of the [`research/`](../../README.md) subtree and is
licensed under the Creative Commons Attribution 4.0 International
license unless otherwise noted. See [`../../LICENSE`](../../LICENSE).
The non-research parts of the repository remain under the GNU General
Public License v3.0 or later as described in
[`../../../README.md`](../../../README.md).
