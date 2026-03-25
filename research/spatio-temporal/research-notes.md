# Pipeline Notes: Spatio-Temporal Argo Modeling

Working notes on the spatiotemporal analysis literature and how it relates to the next phase of this project, including benchmark targets, methodological context, and flagged items to revisit.

---

## Yarger et al. (2022): spatiotemporal benchmarks and framing

Source: Ann. Appl. Stat. 16(1): 216-246, DOI: 10.1214/21-AOAS1477. Full paper reviewed.

### Scope

Yarger et al. (2022) is primarily a spatiotemporal statistics paper whose goal was end-to-end temperature and salinity prediction across the global ocean, including mean estimation, covariance modeling, functional kriging, ocean heat content estimation, mixed layer depth mapping, and density inversion analysis. It is the first comprehensive functional-data analysis of the Argo data.

Their vertical representation step (B-spline smoothing splines, 200 equispaced knots) is a component of this larger system, not its primary contribution. Notes on that vertical step in isolation are in [research-notes.md](/home/jcherry/Documents/storage/git/argo-data-interpolation/research/argo-cycle-representation/research-notes.md). This document covers the spatiotemporal system and its published benchmarks.

### Benchmark metrics (Table 2): spatiotemporal prediction RMSE, temperature

These are leave-one-profile-out cross-validation errors where nearby profiles from other floats are used to predict a held-out profile. Units are °C. Produced across 76,016 temperature profiles spanning 2007-2016.

| Pressure | Metric | RG-type model | KS (Kuusela and Stein 2018) | Yarger FDA |
|---|---|---|---|---|
| 10 dbar | RMSE | 0.6135 | 0.5072 | 0.5215 |
| 10 dbar | Q3 | 0.5026 | 0.3735 | 0.3940 |
| 10 dbar | Median | 0.2556 | 0.1801 | 0.1961 |
| 300 dbar | RMSE | 0.5782 | 0.5124 | **0.4968** |
| 300 dbar | Q3 | 0.4213 | 0.3684 | **0.3644** |
| 300 dbar | Median | 0.1991 | 0.1740 | **0.1720** |
| 1500 dbar | RMSE | 0.1014 | 0.0883 | **0.0857** |
| 1500 dbar | Q3 | 0.0736 | 0.0641 | 0.0689 |
| 1500 dbar | Median | 0.0356 | 0.0311 | 0.0349 |

The FDA model outperforms both baselines at 300 and 1500 dbar. It is slightly worse at 10 dbar, which the paper attributes to spatial correlation lengths that change rapidly near the surface and are not well captured by a fixed number of principal components.

### Benchmark metrics (Table 1): prediction interval coverage

| Variable | Profiles | Pointwise coverage | Band coverage | Nominal |
|---|---|---|---|---|
| Temperature | 76,016 | 96.2% | 95.6% | 95.4% |
| Salinity | 45,188 | 98.2% | 96.6% | 95.4% |

Coverage is slightly conservative and well-calibrated across most of the pressure dimension. The 20 to 200 dbar range does not always achieve full coverage.

### Critical framing: these RMSE values are spatiotemporal, not vertical

Yarger et al.'s RMSE values (~0.50°C at 300 dbar) measure how well nearby profiles from other floats can predict a held-out profile. They include real oceanographic variability not captured by local spatial models, measurement error, and vertical representation error all combined. They are not comparable to per-profile within-cycle fitting RMSE. A well-designed vertical representation should have a fitting error substantially smaller than the spatiotemporal prediction error.

### Key benchmarks to target in the spatiotemporal phase

- Temperature RMSE at 10 dbar: KS=0.5072, Yarger FDA=0.5215
- Temperature RMSE at 300 dbar: KS=0.5124, Yarger FDA=0.4968
- Temperature RMSE at 1500 dbar: KS=0.0883, Yarger FDA=0.0857
- Prediction interval coverage: temperature 96.2% pointwise, 95.6% band (nominal 95.4%)

### Yarger et al.'s identified directions for future improvement (Section 6)

Adaptive bandwidth selection. Allowing scale parameters to change as a function of depth. Iteratively reweighted least squares for mean estimation. Combining estimates across space with uncertainty propagation for global ocean heat content. A functional model that allows rapid changes in the scale parameter as a function of depth would likely improve upon their model at the near-surface.

---

## Kuusela and Stein (2018): the current statistical state of the art

### What they did

Kuusela and Stein developed locally stationary spatiotemporal Gaussian process modeling for Argo temperatures, applying a stationary Matérn covariance model locally at each grid point using data from a moving spatial window. Parameters are estimated by maximum likelihood within each window.

They demonstrated that the Roemmich-Gilson covariance parameters are systematically miscalibrated across depth. Locally estimated Matérn parameters produce better-calibrated prediction intervals. They investigated Student t-distributed measurement errors to handle non-Gaussian heavy tails.

Their method operates at fixed pressure levels: each profile is first linearly interpolated onto the standard grid before spatiotemporal modeling. This pressure-level-by-pressure-level approach treats the vertical and horizontal problems as separable.

### Why this matters for the spatiotemporal phase

Kuusela and Stein (2018) is the closest competitor to Yarger et al. (2022) at 300 and 1500 dbar and slightly better at 10 dbar. Any spatiotemporal method built on top of this pipeline's vertical artifacts should be benchmarked against both KS and Yarger FDA. KS uses fixed-level linear interpolation as its vertical input, which is a direct comparison target: does this pipeline's vertical representation improve the spatiotemporal prediction RMSE of a KS-style model?

---

## Gridded products: context for downstream use

The following products are the primary operational context for spatiotemporal Argo analysis. Understanding how interpolation choices enter each product's methodology is necessary before claiming operational relevance.

**Roemmich-Gilson (2009):** Monthly global fields at 1-degree resolution, 58 fixed pressure levels. Temperature and salinity linearly interpolated onto fixed levels before estimation. The most widely used Argo-derived climatology. Interpolation method choice is embedded in the preprocessing step.

**ISAS (Gaillard et al., 2016):** Univariate OI of anomalies relative to climatology, 0.5-degree grid, 187 standard depth levels. Uses a Gaussian covariance structure.

**EN4 (Good et al., 2013):** Monthly objective analyses with explicit uncertainty estimates and iterative background error treatment. Notable for including analysis uncertainty in distributed fields.

**CARS (Ridgway et al., 2002):** Weighted least-squares smoothing with regional and topographic treatment, particularly suited to boundary current regions.

**MIMOC (Schmidtko et al., 2013):** Monthly isopycnal climatology. Maps on isopycnal surfaces rather than depth or pressure levels, better preserving water-mass structure across fronts.

**4D-MGA (Zhou et al., 2023):** Higher-resolution spatiotemporal multigrid analysis targeting finer-scale variability.

### TO DO: understand the full Argo scientific analysis pipeline

The raw profile preservation vs. interpolation distinction implies a chain of processing steps between a float surfacing and a researcher using a gridded climate product. Interpolation method choices enter that chain at specific, identifiable points.

Understanding this in detail matters for two reasons. First, it determines exactly where this pipeline's artifacts would slot into operational use: a replacement for the interpolation step inside Roemmich and Gilson, an alternative input format for EN4 or ISAS, or a preprocessing step before GP-based spatiotemporal analysis. Second, knowing where QC flags, bias corrections, and delayed-mode processing enter the chain clarifies what state the data is in when it reaches the vertical representation step.

Recommended reading: Wong et al. (2020) for the delayed-mode QC pipeline, Roemmich and Gilson (2009) for how interpolation enters the standard-level gridded product, Argo data management documentation at https://argo.ucsd.edu/data/data-management/, and Yarger et al. (2022) Section 2.1 and 2.2 for a concise processing context overview from a statistical user's perspective.

---

## ML surface-to-depth inference literature

### What this literature does

These papers solve a cross-domain prediction problem: given only surface observations (sea surface temperature from satellites, sea surface height from altimetry, surface salinity), infer the full temperature and salinity structure at depth. The output is a volume or a profile at each horizontal location. "Subsurface structure" in this context means the vertical arrangement of water properties below the surface, not seafloor topography.

Key papers: Buongiorno Nardelli (2020) used stacked LSTM with Monte Carlo dropout for hydrographic profile retrieval from surface predictors. Su et al. (2022) used ConvLSTM to reconstruct global subsurface temperature fields. Chen et al. (2023) and Miranda et al. (2025) combine neural networks with EOF/PCA coefficient representations.

### Why it is not relevant to the current phase

This pipeline assumes a measured profile already exists and asks how to represent it compactly and accurately. The ML surface-to-depth work is upstream inference: it asks how to generate a profile where none was measured. These are not competing approaches. They address different steps in the data pipeline.

### Why it will be useful in the spatiotemporal phase

When the project moves to spatiotemporal interpolation, the problem of estimating profiles at unobserved locations becomes central. This is the same surface-to-depth inference problem this literature addresses.

Three specific connections worth investigating.

First, the feature engineering choices in these papers, particularly what surface observables correlate most strongly with subsurface structure at different depth ranges and latitudes, are directly relevant to designing input features for a spatiotemporal model.

Second, the uncertainty estimation approaches, particularly Buongiorno Nardelli's Monte Carlo dropout and the EOF/PCA coefficient methods, represent alternative architectures for generating calibrated uncertainty estimates over the full water column. These are natural comparison targets.

Third, this literature has already benchmarked regional and global predictive skill across a range of architectures. Those benchmarks provide context for what spatiotemporal RMSE levels are achievable with learned approaches, complementing the Yarger et al. Table 2 metrics.

Return to Buongiorno Nardelli (2020), Su et al. (2022), Chen et al. (2023), and Miranda et al. (2025) when designing the spatiotemporal layer. Focus on: what surface features they use as predictors, what depth ranges they perform well and poorly on, and how they quantify uncertainty over the full profile.

---

## EOF/PCA methods

### What EOF/PCA actually does

EOF and PCA applied to oceanographic profiles are dimensionality reduction techniques applied across many profiles simultaneously, not within a single profile. The procedure takes a large collection of profiles, stacks them as rows in a matrix, and decomposes that matrix to find dominant patterns of variability across the dataset. The first EOF might represent seasonal thermocline deepening, the second a halocline signal, and so on.

Projecting a single profile onto the EOF basis produces a compact set of scores that approximately reconstruct it. This is global compression: the basis functions are learned from the whole dataset, so the representation of any individual profile is only as good as how well it fits the population-level patterns. Unusual profiles with atypical thermocline depths or double haloclines will be poorly represented.

### Why Pauthenet et al. and Maze et al. are spatiotemporal, not vertical

Pauthenet et al. (2019) use multivariate functional PCA to classify water masses and analyze thermohaline variance. The vertical structure is the input feature; the analysis is horizontal, across the ocean.

Maze et al. (2017) apply Gaussian mixture models to PCA-reduced Argo temperature profiles to identify coherent spatial heat pattern regimes in the North Atlantic. Again, vertical structure is input, horizontal regime boundaries are output.

Both papers are using vertical structure as a feature for horizontal spatial analysis. Neither is improving or replacing the vertical representation of individual profiles.

### Why they will be useful in the spatiotemporal phase

EOF/PCA scores have been used extensively as input features for spatiotemporal kriging schemes and ML models predicting subsurface structure. When building the spatiotemporal layer, derived features from this pipeline's spline fits (thermocline depth, mixed layer depth, gradient magnitude at key pressure levels, knot positions themselves) are natural analogues to the EOF scores used in this literature, and may be more informative because they are adaptive to each individual profile's structure rather than projected onto a global basis.

Return to Pauthenet et al. (2019) and Maze et al. (2017) for reference on what profile features carry the most spatiotemporal predictive information.

---

## Park et al. (2023): debiased latent GP

Park et al. developed a debiased latent Gaussian process formulation for global ocean heat transport estimation with full uncertainty quantification, addressing systematic biases that arise when applying standard GP methods to sparse and irregularly sampled Argo data. Their approach is particularly relevant for estimating integral functionals such as heat transport rather than pointwise temperature values.

This represents the current frontier of principled uncertainty quantification in Argo spatiotemporal analysis and is a natural methodological reference for the spatiotemporal phase alongside Kuusela and Stein (2018).

---

## Uncertainty quantification across methods: what the spatiotemporal phase needs to match

Gridded products do produce uncertainty estimates, EN4 being the most notable. But those uncertainties reflect horizontal mapping error: the uncertainty from interpolating spatially across sparse float coverage. They do not reflect uncertainty in the vertical representation of any individual profile, and they do not vary with depth in a physically motivated way.

Kuusela and Stein (2018) and Park et al. (2023) represent the frontier of principled uncertainty quantification in Argo spatiotemporal analysis, using full GP frameworks that propagate covariance through the estimation. Those uncertainties describe the horizontal mapping problem, not the vertical profile representation problem.

This distinction matters for the spatiotemporal phase: when building a spatiotemporal model on top of this pipeline's vertical artifacts, the total output uncertainty will have two separable components. The first is the vertical representation uncertainty from the spline fit (already computed per-cycle, depth-varying, physically decomposed into three named sources). The second is the spatiotemporal prediction uncertainty from the mapping layer. The existing literature provides good methodology for the second component. The first component is what this pipeline adds to the chain.

Any spatiotemporal phase evaluation should assess whether propagating the per-profile depth-varying uncertainty through the spatiotemporal model improves prediction interval coverage relative to methods that ignore vertical representation uncertainty.

---

## Li et al. (2022): climate motivation for the entire enterprise

Li et al. (2022) showed that using linear interpolation rather than MRST-PCHIP yielded ocean heat content warming trends approximately 14% lower over the 1956-2020 historical record, corresponding to approximately 40 Zeta Joules and a thermosteric sea level rise underestimate of 0.55 mm/yr.

Ocean heat content estimation is a primary stated application of Yarger et al. (2022) and Park et al. (2023). The spatiotemporal phase of this project ultimately aims to produce ocean state estimates that feed into exactly these downstream climate diagnostics. Li et al. (2022) establishes that the quality of vertical representation entering those estimates has a quantified, climate-scale effect. Getting the vertical step right before building the spatiotemporal layer is therefore not just a preprocessing choice but a scientifically motivated priority with demonstrable downstream consequences.
