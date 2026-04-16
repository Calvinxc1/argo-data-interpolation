# Underwater Acoustics Notebooks

This folder indexes prototype notebooks for the `underwater-acoustics` topic. These notebooks are experiment artifacts, not canonical summaries. Source-backed claims should trace back through [../literature-review.md](../literature-review.md), with notebook-specific interpretations kept tied to the actual saved experiment state.

Committed notebooks in this folder are paired with Jupytext `.py` files in percent format. The `.ipynb` remains the primary runnable research artifact; the paired `.py` file exists to make notebook content easier to diff, review, and search in version control.

## Sequence

These notebooks are intended to be read as a four-step progression:

1. [1-jana-study-replication.ipynb](1-jana-study-replication.ipynb) and [1-jana-study-replication.py](1-jana-study-replication.py): establish the calibrated Jana et al. (2022) replication baseline, from archive pull through the reproduced domain, map, and subdomain figures.
2. [2-jana-holdout-validation.ipynb](2-jana-holdout-validation.ipynb) and [2-jana-holdout-validation.py](2-jana-holdout-validation.py): turn that descriptive replication into an explicit held-out benchmark by evaluating a flat Jana-style `2° x 2°` retained-cycle kernel predictor by depth.
3. [3-uncertainty-extension.ipynb](3-uncertainty-extension.ipynb) and [3-uncertainty-extension.py](3-uncertainty-extension.py): keep the same strict retained archive and holdout protocol, but replace the flat local mean with a weighted retained-cycle predictor to test whether modest spatio-temporal weighting improves skill.
4. [4-uncertainty-extension-all-cycles.ipynb](4-uncertainty-extension-all-cycles.ipynb) and [4-uncertainty-extension-all-cycles.py](4-uncertainty-extension-all-cycles.py): keep the weighted local-window idea from notebook `3`, but relax the archive-pruning rules so partially sampled cycles can contribute where they have real depth support.

## License

This folder is part of the [`research/`](../../README.md) subtree and is
licensed under the Creative Commons Attribution 4.0 International
license unless otherwise noted. See [`../../LICENSE`](../../LICENSE).
The non-research parts of the repository remain under the GNU General
Public License v3.0 or later as described in
[`../../../README.md`](../../../README.md).
