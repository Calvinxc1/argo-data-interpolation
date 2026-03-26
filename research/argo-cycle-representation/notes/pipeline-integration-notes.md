# Pipeline Integration Notes: Argo Cycle Representation

These notes track where the cycle-level vertical artifact may fit into the broader Argo processing and downstream analysis chain. Source-backed processing claims should trace to [../literature-review.md](../literature-review.md).

## Understand the full Argo scientific analysis pipeline

The raw profile preservation vs. interpolation distinction implies a chain of processing steps between a float surfacing and a researcher using a gridded climate product. Interpolation method choices enter that chain at specific, identifiable points.

Understanding this in detail matters for two reasons. First, it determines exactly where this pipeline's artifacts would slot into operational use: a replacement for the interpolation step inside Roemmich and Gilson, an alternative input format for EN4 or ISAS, or a preprocessing step before GP-based spatiotemporal analysis. Second, knowing where QC flags, bias corrections, and delayed-mode processing enter the chain clarifies what state the data is in when it reaches the vertical representation step.

Recommended reading: Wong et al. (2020) for the delayed-mode QC pipeline, Roemmich and Gilson (2009) for how interpolation enters the standard-level gridded product, Argo data management documentation at `https://argo.ucsd.edu/data/data-management/`, and Yarger et al. (2022) Section 2.1 and 2.2 for a concise processing context overview from a statistical user's perspective.

Follow-up item for a future version: account for measurement-time lag within Argo profiles. In the current pipeline design, a profile is treated as effectively static over the interval between subsurface measurement and later surface or report time. This is a simplifying implementation assumption. A future version should evaluate whether the within-cycle temporal offset is large enough to affect interpolation quality or uncertainty, especially when combining the vertical artifact with downstream spatiotemporal modeling.
