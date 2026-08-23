# Underwater Acoustics Notebooks

This folder indexes prototype notebooks for the `underwater-acoustics` topic. These notebooks are experiment artifacts, not canonical summaries. Source-backed claims should trace back through [../literature-review.md](../literature-review.md), with notebook-specific interpretations kept tied to the actual saved experiment state.

Committed notebooks in this folder are paired with Jupytext `.py` files in percent format. The `.ipynb` remains the primary runnable research artifact; the paired `.py` file exists to make notebook content easier to diff, review, and search in version control.

Each notebook is intended to run independently. They share a conceptual sequence, but they no longer depend on cached archives or saved validation outputs from earlier notebooks in the folder.

These notebooks are a record of runs rather than a maintained example suite; see [../../notebook-currency.md](../../notebook-currency.md) for which parts have fallen behind the current package.

The local `lib/` package holds notebook-support code used only for this topic's reproducibility and diagnostics, including weighting helpers, validation-query helpers, prediction utilities, and plotting helpers.

## Sequence

These notebooks are intended to be read as a six-step progression. The sequence is not just chronological; each notebook answers one narrower question and then hands the result to the next:

1. establish a calibrated replication baseline
2. turn that baseline into an explicit held-out benchmark
3. test whether weighting improves that benchmark without changing the archive
4. test whether relaxing the archive improves the same weighted predictor
5. repackage the preferred deterministic path as a reusable local model surface
6. build the separate TEOS-10 sound-speed uncertainty product from that deterministic surface

Read together, the story moves from descriptive replication, to predictive validation, to controlled method changes, to a deterministic model-build handoff, and then to the paper-support uncertainty product.

That progression maps onto the current notebook set as follows:

1. [1-jana-study-replication.ipynb](1-jana-study-replication.ipynb) and [1-jana-study-replication.py](1-jana-study-replication.py): establish the calibrated Jana et al. (2022) replication baseline, from archive pull through the reproduced domain, map, and subdomain figures. This notebook settles the descriptive starting point that the rest of the sequence can interrogate.
2. [2-jana-holdout-validation.ipynb](2-jana-holdout-validation.ipynb) and [2-jana-holdout-validation.py](2-jana-holdout-validation.py): turn that descriptive replication into an explicit held-out benchmark by evaluating a flat Jana-style `2° x 2°` retained-cycle kernel predictor by depth. This notebook converts the replication archive into the first predictive baseline.
3. [3-uncertainty-extension.ipynb](3-uncertainty-extension.ipynb) and [3-uncertainty-extension.py](3-uncertainty-extension.py): keep the same strict retained archive and holdout protocol, but replace the flat local mean with a weighted retained-cycle predictor to test whether modest spatio-temporal weighting improves skill. This notebook changes the predictor while keeping the archive fixed.
4. [4-uncertainty-extension-all-cycles.ipynb](4-uncertainty-extension-all-cycles.ipynb) and [4-uncertainty-extension-all-cycles.py](4-uncertainty-extension-all-cycles.py): keep the weighted local-window idea from notebook `3`, but relax the archive-pruning rules so partially sampled cycles can contribute where they have real depth support. This notebook changes the archive while keeping the weighted predictor idea.
5. [5-uncertainty-model-build.ipynb](5-uncertainty-model-build.ipynb) and [5-uncertainty-model-build.py](5-uncertainty-model-build.py): rebuild the relaxed weighted local-window model as the current deterministic backbone when needed, cache it under `data/uncertainty_model_build.pkl`, and export passthrough-ready model tables without yet attaching uncertainty propagation. This notebook is the handoff from the experimental sequence into reusable model-build work.
6. [6-sound-speed-uncertainty-product.ipynb](6-sound-speed-uncertainty-product.ipynb) and [6-sound-speed-uncertainty-product.py](6-sound-speed-uncertainty-product.py): build the OCEANS 2026 paper-support uncertainty product as a separate table-producing pipeline, including componentized temperature/salinity variance, a depthwise spatial variance bucket, GSW/TEOS-10 sound-speed propagation, support diagnostics, and 110 m figure-ready exports. Three of this notebook's 110 m exports also appear as Fig. 1 of the OCEANS 2026 Monterey paper; see [../notes/paper-figure-provenance.md](../notes/paper-figure-provenance.md).

## License

This folder is part of the [`research/`](../../README.md) subtree and is
licensed under the Creative Commons Attribution 4.0 International
license unless otherwise noted. See [`../../LICENSE`](../../LICENSE).
The non-research parts of the repository remain under the GNU General
Public License v3.0 or later as described in
[`../../../README.md`](../../../README.md).
