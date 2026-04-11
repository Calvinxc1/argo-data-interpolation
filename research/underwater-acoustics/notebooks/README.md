# Underwater Acoustics Notebooks

This folder indexes prototype notebooks for the `underwater-acoustics` topic. These notebooks are experiment artifacts, not canonical summaries. Source-backed claims should trace back through [../literature-review.md](../literature-review.md), with notebook-specific interpretations kept tied to the actual saved experiment state.

Committed notebooks in this folder are paired with Jupytext `.py` files in percent format. The `.ipynb` remains the primary runnable research artifact; the paired `.py` file exists to make notebook content easier to diff, review, and search in version control.

## Files

- [jana-study-replication.ipynb](jana-study-replication.ipynb) and [jana-study-replication.py](jana-study-replication.py): replication notebook for Jana et al. (2022), covering Argo data pull and filtering, profile interpolation, sound-speed calculation, and the figure-reproduction workflow through the current subdomain composites.

## License

This folder is part of the [`research/`](../../README.md) subtree and is
licensed under the Creative Commons Attribution 4.0 International
license unless otherwise noted. See [`../../LICENSE`](../../LICENSE).
The non-research parts of the repository remain under the GNU General
Public License v3.0 or later as described in
[`../../../README.md`](../../../README.md).
