# Spatio-Temporal Argo Modeling: A Literature Review

This review covers methods and findings relevant to spatiotemporal interpolation, reconstruction, and analysis of Argo oceanographic data, including objective mapping products, Gaussian process methods, functional data analysis, machine learning approaches, and reduced-order profile representations.

---

## Operational Argo Processing Context

Core Argo GDAC processing preserves observed profile levels through quality-control stages. Interpolation is introduced mainly when generating standard-level or gridded derivative products. Real-time and delayed-mode pipelines prioritize QC flags and bias corrections rather than replacing original vertical sampling (Wong et al., 2020). The Argo data management chain proceeds in two stages. Real-time QC is applied within 24 hours of data receipt. Delayed-mode QC follows 6 to 12 months after collection, involving expert review, conductivity sensor drift correction via the Owens-Wong-Cabanes (OWC) method, and pressure bias correction. Delayed-mode files carry DATA_MODE = 'D'.

Sensor error bounds from this processing chain are the measurement noise floor that all spatiotemporal models and gridded products must contend with. Standard SBE CTD floats carry PRES_ADJUSTED_ERROR = 2.4 dbar (constant), TEMP_ADJUSTED_ERROR = 0.002°C, and PSAL_ADJUSTED_ERROR = maximum(adjustment uncertainty, 0.01) PSU (Wong, Keeley, Carval and the Argo Data Management Team, 2025). Approximately 15% of floats deployed after 2015 experienced abrupt salty conductivity drift (Wong et al., 2023), making delayed-mode adjusted salinity the only reliable input for research applications sensitive to salinity errors. Uncorrectable profiles with PRES_ADJUSTED_ERROR = 20 dbar (Truncated Negative Pressure Drift in APEX floats with APF8 or earlier controllers) should be excluded from global change research applications (Barker et al., 2011; Wong et al., 2025). Full sensor error characterization and the TNPD issue are documented in the companion vertical literature review.

---

## Climate Motivation: Interpolation Method Choice at Scale

Li et al. (2022) demonstrated that the choice of vertical interpolation method materially affects downstream climate estimates. Using linear interpolation rather than MRST-PCHIP yielded ocean heat content warming trends approximately 14% lower over the 1956-2020 historical record, corresponding to approximately 40 Zeta Joules and a thermosteric sea level rise underestimate of 0.55 mm/yr. Ocean heat content estimation and thermosteric sea level rise are primary applications of the spatiotemporal gridded products and GP methods described in this review. The quality of vertical representation entering these analyses has a quantified, climate-scale effect on their outputs.

---

## Gridded Argo Products and Objective Mapping

Large-scale reconstruction of the ocean state from Argo profiles requires interpolating irregularly distributed float observations onto regular grids in space, time, and depth. The dominant framework is optimal interpolation (OI), also known as kriging or objective analysis depending on the community. Each approach involves specifying a mean and covariance structure, then using these to form a minimum mean-squared-error linear prediction at unobserved locations. The resulting gridded products are the primary interface between Argo observations and downstream climate science.

**Roemmich-Gilson Argo Climatology (Roemmich and Gilson, 2009)** provides monthly global temperature and salinity fields at 1-degree resolution across 58 fixed non-uniformly spaced pressure levels. Mean estimation uses weighted local regression combining data from 2004 to 2016 with the 100 nearest profiles per month and pressure level. Anomalies are mapped using a covariance function with non-stationary parameters that increase zonal correlation range in the tropics. Temperature and salinity are interpolated onto fixed pressure levels before estimation, using the 58-level grid as the vertical standard.

**ISAS (Gaillard et al., 2016)** performs univariate OI of anomalies relative to a background climatology on a 0.5-degree grid with 187 standard depth levels, using a Gaussian covariance structure. It operates on anomaly fields after subtraction of a reference climatology, targeting mesoscale and interannual variability.

**EN4 (Good et al., 2013)** provides quality-controlled global ocean temperature and salinity profiles and monthly objective analyses with explicit uncertainty estimates. It applies iterative background error treatment and includes explicit uncertainty quantification in its gridded fields, making it notable among operational products for its treatment of analysis error.

Pending local full-text review in this topic, two earlier objective-analysis references sharpen the lineage behind these Argo-era products. Ishii, Kimoto, and Kachi (2003) appear to be an important historical antecedent because they pair historical subsurface temperature analysis with explicit error estimates rather than treating mapping as uncertainty-free bookkeeping. Chang et al. (2009) then appear to carry that logic into the 21st-century Argo era through monthly global temperature and salinity objective analyses positioned against World Ocean Atlas and assimilation-validation use cases. Together, those two references would strengthen the review's current mapped-product section by making the transition from pre-Argo error-estimated analyses to Argo-era monthly objective analyses more explicit.

**CARS (Ridgway et al., 2002)** uses weighted least-squares smoothing with regional and topographic treatment, with particular attention to boundary current regions. Its four-dimensional weighted least-squares framework accommodates the complex flow geometries of regions such as the western boundary currents around Australasia.

**MIMOC (Schmidtko et al., 2013)** is a monthly isopycnal upper-ocean climatology with mixed layers. Its distinctive contribution is mapping on isopycnal rather than depth or pressure surfaces, which better preserves water-mass structure across fronts and avoids smearing across density contrasts that depth-level mapping introduces.

**4D-MGA (Zhou et al., 2023)** presents a higher-resolution spatiotemporal multigrid analysis with improved validation skill relative to climatological baselines, targeting finer-scale variability that standard-resolution products cannot capture.

---

## Gaussian Process Approaches

### Locally stationary covariance modeling

Kuusela and Stein (2018) introduced locally stationary spatiotemporal Gaussian process modeling for Argo temperatures, applying a stationary Matérn covariance model locally at each grid point using data from a moving spatial window. This addresses the non-stationarity of ocean temperature fields without requiring explicit modeling of the non-stationary covariance structure. Parameters are estimated by maximum likelihood within each window and used for local kriging prediction. Kuusela and Stein demonstrated that the Roemmich-Gilson covariance parameters are systematically miscalibrated at many depths, and that locally estimated Matérn parameters produce better-calibrated prediction intervals. They also investigated Student t-distributed measurement errors to handle non-Gaussian heavy tails in ocean temperature data. Their cross-validation results show clear improvements in point predictions and uncertainty calibration over the existing state of the art, and demonstrate that accounting for non-stationarity and non-Gaussianity is crucial for obtaining well-calibrated uncertainties.

Kuusela and Stein (2018) note that their method operates at fixed pressure levels, with each profile first linearly interpolated onto the standard grid before spatiotemporal modeling. This pressure-level-by-pressure-level approach treats the vertical and horizontal problems as separable.

### Debiased latent GP for heat transport

Park et al. (2023) developed a debiased latent Gaussian process formulation for global ocean heat transport estimation with full uncertainty quantification. Their approach addresses systematic biases that arise when applying standard GP methods to sparse and irregularly sampled Argo data, particularly in the context of estimating integral functionals such as heat transport rather than pointwise temperature values.

---

## Functional Data Analysis

### Spatiotemporal functional kriging for Argo profiles

Yarger, Stoev, and Hsing (2022) provided the first comprehensive functional-data analysis of the Argo data, developing spatiotemporal functional kriging methodology for mean and covariance estimation to predict temperature and salinity at a fixed location as a smooth function of depth. Their approach combines smoothing splines (to represent each profile as a continuous function of pressure), local polynomial regression (to smooth the mean function in space and time), and multivariate spatial modeling of functional principal component scores.

The vertical representation step in Yarger et al. (2022) uses B-spline smoothing splines with 200 equispaced knots over [0, 2000] dbar, with GCV for smoothing parameter selection. Smoothing parameters are chosen as fixed ratios collapsed into a single 1D search. The working within-profile correlation structure uses a Markovian form that helps stabilize the spline estimation for irregularly sampled profiles.

After estimating a spatially varying functional mean by local regression, residual covariance is modeled using functional principal components (FPCs). Each profile is summarized by its FPC scores, and a Matérn space-time covariance model is fitted jointly to the decorrelated scores of temperature and salinity. This joint modeling of temperature and salinity enables prediction and uncertainty estimation for derived quantities such as potential density and ocean heat content.

Cross-validation results (Table 2, Yarger et al., 2022) from leave-one-profile-out prediction across 76,016 temperature profiles spanning 2007 to 2016 show the following spatiotemporal prediction RMSE in °C:

| Pressure | RG-type model | Kuusela and Stein | Yarger FDA |
|---|---|---|---|
| 10 dbar | 0.6135 | 0.5072 | 0.5215 |
| 300 dbar | 0.5782 | 0.5124 | 0.4968 |
| 1500 dbar | 0.1014 | 0.0883 | 0.0857 |

The FDA model outperforms both the RG-type reference model and Kuusela and Stein at 300 and 1500 dbar. It performs slightly worse at 10 dbar, which the authors attribute to spatial correlation lengths that change rapidly near the surface and are not well captured by a fixed number of principal components.

Prediction interval coverage (Table 1, Yarger et al., 2022) across 76,016 temperature profiles: 96.2% pointwise and 95.6% band coverage against a nominal 95.4% level. Coverage for salinity across 45,188 profiles: 98.2% pointwise and 96.6% band. The paper notes that the 20 to 200 dbar range does not always achieve full coverage.

Key advantages identified by Yarger et al. (2022) over pressure-level methods include: avoiding interpolation error for sparsely observed profiles, leveraging all measurements from each profile rather than only those near standard levels, computational gains from sharing information across pressure, and natural availability of derivative and integral estimates for oceanographic functionals. Their functional approach can provide predictions for all pressure levels in approximately the same time as computing a pointwise approach for 13 pressure levels, yielding roughly a four to five times speedup over computing all 58 Roemmich-Gilson levels.

The paper identifies several directions for future improvement, including adaptive bandwidth selection, allowing scale parameters to change as a function of depth, and combining estimates across space with uncertainty propagation.

### Functional regression for BGC Argo

Korte-Stapff, Yarger, Stoev, and Hsing (2026, Journal of the Royal Statistical Society Series C) extended the Yarger et al. framework to biogeochemical Argo data, introducing a functional regression model for oxygen profiles in the Southern Ocean with temperature and salinity as functional predictors. Their mixture model approach accommodates the spatial frontal structure of the Southern Ocean and provides spatially dependent predictions onto a grid.

---

## Machine Learning and Surface-to-Depth Inference

A substantial body of work addresses the problem of inferring subsurface temperature and salinity profiles from surface observations. Surface properties such as sea surface temperature, sea surface height from altimetry, and surface salinity are observable from satellites globally and continuously. Subsurface structure at depth is not. These methods learn statistical mappings from surface patterns to the full water column, enabling reconstruction of subsurface fields without requiring concurrent in situ measurements.

**Buongiorno Nardelli (2020)** applied a stacked LSTM architecture with Monte Carlo dropout to retrieve hydrographic temperature and salinity profiles from combined satellite and in situ surface measurements. The Monte Carlo dropout approach provides approximate Bayesian uncertainty estimates over the full profile. The method was validated against withheld Argo profiles and demonstrates meaningful predictive skill in the upper 2000 m.

**Su et al. (2022)** employed a ConvLSTM architecture to reconstruct global subsurface temperature fields from 1993 to 2020 using satellite sea surface observations. The ConvLSTM captures spatiotemporal dependencies in the surface fields and propagates them into subsurface reconstructions.

**Chen et al. (2023)** combined deep neural networks with deep evidential regression to reconstruct subsurface temperature profiles globally, providing explicit uncertainty estimates on the predicted profiles. Their approach uses EOF decomposition of the target profiles as a reduced-order representation for the network output.

**Miranda et al. (2025)** developed NeSPReSO (Neural Synthetic Profiles from Remote Sensing and Observations) for reconstruction of temperature and salinity fields in the Gulf of Mexico, using regional Argo data and satellite observations as inputs. The study demonstrates the sensitivity of these methods to regional dynamics and data availability.

These studies collectively demonstrate that surface-to-depth inference methods can achieve substantial predictive skill but are closely tied to the specific ocean region, the feature engineering choices for surface inputs, and the availability of dense in situ training data. Uncertainty estimation approaches vary considerably across studies, from Bayesian approximate inference to empirical ensemble methods.

---

## EOF/PCA and Reduced-Order Profile Representations

Empirical Orthogonal Function (EOF) and principal component analysis applied to oceanographic profiles provide compact representations of dominant profile variability by decomposing a large collection of profiles into a set of basis functions and per-profile scores. The first few EOF modes typically capture a large fraction of the variance across the dataset, providing an efficient basis for regime identification and statistical modeling.

**Pauthenet et al. (2019)** applied multivariate functional PCA to characterize the thermohaline modes of the global ocean, demonstrating that a small number of joint temperature-salinity EOF modes explain most thermohaline variance in climatological fields. The functional PCA framework treats profiles as continuous curves rather than discrete vectors, enabling analysis of the full vertical structure without commitment to fixed depth levels.

**Maze et al. (2017)** applied unsupervised Gaussian mixture models to PCA-reduced Argo temperature profiles to identify coherent spatial heat patterns in the North Atlantic Ocean. The approach reveals physically meaningful regime boundaries corresponding to known oceanographic features such as the subpolar front and subtropical gyre. The study demonstrates that unsupervised classification of PCA-compressed profiles can extract oceanographically interpretable structure without requiring labeled training data.

Both studies use vertical structure as input features for horizontal spatial analysis: identifying water masses, regime boundaries, and spatial patterns across the ocean. EOF/PCA scores derived from Argo profiles have become standard input features for spatiotemporal kriging schemes, ML models predicting subsurface structure, and water mass classification systems.

---

## References

- Barker, P. M., Dunn, J. R., Domingues, C. M., & Wijffels, S. E. (2011). [Pressure sensor drifts in Argo and their impacts](../argo-cycle-representation/sources/barker-2011-pressure_sensor_drifts_in_argo.pdf). *Journal of Atmospheric and Oceanic Technology, 28*(8), 1036–1049. https://doi.org/10.1175/2011JTECHO831.1
- Buongiorno Nardelli, B. (2020). A deep learning network to retrieve ocean hydrographic profiles from combined satellite and in situ measurements. *Remote Sensing, 12*(19), 3151. https://doi.org/10.3390/rs12193151
- Chang, Y.-S., Rosati, A. J., Zhang, S., & Harrison, M. J. (2009). Objective analysis of monthly temperature and salinity for the world ocean in the 21st century: Comparison with World Ocean Atlas and application to assimilation validation. *Journal of Geophysical Research: Oceans, 114*, C02014. https://doi.org/10.1029/2008JC004970
- Chen, C., Liu, Z., Li, Y., & Yang, K. (2023). Reconstructing subsurface temperature profiles with sea surface data worldwide through deep evidential regression methods. *Deep-Sea Research Part I, 197*, 104054. https://doi.org/10.1016/j.dsr.2023.104054
- Gaillard, F., Reynaud, T., Thierry, V., Kolodziejczyk, N., & von Schuckmann, K. (2016). [In situ-based reanalysis of the global ocean temperature and salinity with ISAS](../underwater-acoustics/sources/gaillard-2016-in_situ_based_reanalysis_global_ocean_temperature_salinity_isas.pdf). *Journal of Climate, 29*(4), 1305–1323. https://doi.org/10.1175/JCLI-D-15-0028.1
- Good, S. A., Martin, M. J., & Rayner, N. A. (2013). [EN4: Quality controlled ocean temperature and salinity profiles and monthly objective analyses with uncertainty estimates](../underwater-acoustics/sources/good-2013-en4_quality_controlled_ocean_temperature_salinity_profiles_monthly_objective_analyses.pdf). *Journal of Geophysical Research: Oceans, 118*(12), 6704–6716. https://doi.org/10.1002/2013JC009067
- Ishii, M., Kimoto, M., & Kachi, M. (2003). Historical ocean subsurface temperature analysis with error estimates. *Monthly Weather Review, 131*(1), 51–73. https://doi.org/10.1175/1520-0493(2003)131<0051:HOSTAW>2.0.CO;2
- Korte-Stapff, M., Yarger, D., Stoev, S., & Hsing, T. (2026). A functional regression model for heterogeneous BioGeoChemical Argo data in the Southern Ocean. *Journal of the Royal Statistical Society Series C: Applied Statistics, 75*(1), 79–99. https://doi.org/10.1093/jrsssc/qlaf036
- Kuusela, M., & Stein, M. L. (2018). [Locally stationary spatio-temporal interpolation of Argo profiling float data](../underwater-acoustics/sources/kuusela-2018-locally_stationary_spatiotemporal_interpolation.pdf). *Proceedings of the Royal Society A, 474*(2220), 20180400. https://doi.org/10.1098/rspa.2018.0400
- Maze, G., Mercier, H., Fablet, R., Tandeo, P., Lopez Radcenco, M., Lenca, P., Feucher, C., & Le Goff, C. (2017). Coherent heat patterns revealed by unsupervised classification of Argo temperature profiles in the North Atlantic Ocean. *Progress in Oceanography, 151*, 275–292. https://doi.org/10.1016/j.pocean.2016.12.008
- Li, Y., Church, J. A., McDougall, T. J., & Barker, P. M. (2022). [Sensitivity of observationally based estimates of ocean heat content and thermal expansion to vertical interpolation schemes](../argo-cycle-representation/sources/li-2022-ocean_heat_content_interpolation_sensitivity.pdf). *Geophysical Research Letters, 49*(24), e2022GL101079. https://doi.org/10.1029/2022GL101079
- Miranda, J. R., et al. (2025). Neural synthetic profiles from remote sensing and observations (NeSPReSO). *Ocean Modelling, 196*, 102550. https://doi.org/10.1016/j.ocemod.2025.102550
- Park, B., Kuusela, M., Giglio, D., & Gray, A. (2023). Spatiotemporal local interpolation of global ocean heat transport using Argo floats: A debiased latent Gaussian process approach. *The Annals of Applied Statistics, 17*(2), 1491–1520. https://doi.org/10.1214/22-AOAS1679
- Pauthenet, E., Roquet, F., Madec, G., Sallee, J.-B., & Nerini, D. (2019). The thermohaline modes of the global ocean. *Journal of Physical Oceanography, 49*(10), 2535–2552. https://doi.org/10.1175/JPO-D-19-0120.1
- Ridgway, K. R., Dunn, J. R., & Wilkin, J. L. (2002). Ocean interpolation by four-dimensional weighted least squares. *Journal of Atmospheric and Oceanic Technology, 19*(9), 1357–1375. https://doi.org/10.1175/1520-0426(2002)019<1357:OIBFDW>2.0.CO;2
- Roemmich, D., & Gilson, J. (2009). [The 2004–2008 mean and annual cycle of temperature, salinity, and steric height in the global ocean from the Argo Program](../underwater-acoustics/sources/roemmich-2009-mean_annual_cycle_temperature_salinity_steric_height_global_ocean_argo.pdf). *Progress in Oceanography, 82*(2), 81–100. https://doi.org/10.1016/j.pocean.2009.03.004
- Schmidtko, S., Johnson, G. C., & Lyman, J. M. (2013). [MIMOC: A global monthly isopycnal upper-ocean climatology with mixed layers](../underwater-acoustics/sources/schmidtko-2013-mimoc_global_monthly_isopycnal_upper_ocean_climatology_with_mixed_layers.pdf). *Journal of Geophysical Research: Oceans, 118*(4), 1658–1672. https://doi.org/10.1002/jgrc.20122
- Su, H., Jiang, J., Wang, A., Zhuang, W., & Yan, X.-H. (2022). Subsurface temperature reconstruction for the global ocean from 1993 to 2020 using satellite observations and deep learning. *Remote Sensing, 14*(13), 3198. https://doi.org/10.3390/rs14133198
- Wong, A. P. S., Gilson, J., & Cabanes, C. (2023). [Argo salinity: bias and uncertainty evaluation](../argo-cycle-representation/sources/wong-2023-argo_salinity.pdf). *Earth System Science Data, 15*(1), 383–393. https://doi.org/10.5194/essd-15-383-2023
- Wong, A. P. S., Wijffels, S. E., Riser, S. C., et al. (2020). [Argo data 1999–2019: Two million temperature-salinity profiles and subsurface velocity observations from a global array of profiling floats](../argo-cycle-representation/sources/wong-2020-argo_data_1999_2019.pdf). *Frontiers in Marine Science, 7*, 700. https://doi.org/10.3389/fmars.2020.00700
- Wong, A. P. S., Keeley, R., Carval, T., and the Argo Data Management Team (2025). [Argo Quality Control Manual for CTD and Trajectory Data](../argo-cycle-representation/sources/wong-2025-argo_qc_manual.pdf). Version 3.9. https://doi.org/10.13155/33951
- Yarger, D., Stoev, S., & Hsing, T. (2022). [A functional-data approach to the Argo data](../argo-cycle-representation/sources/yarger-2022-functional_data_approach_to_argo.pdf). *The Annals of Applied Statistics, 16*(1), 216–246. https://doi.org/10.1214/21-AOAS1477
- Zhou, B., et al. (2023). [High-resolution gridded temperature and salinity fields from Argo floats based on a spatiotemporal four-dimensional multigrid analysis method](../underwater-acoustics/sources/zhou-2023-high_resolution_gridded_temperature_salinity_fields_argo_spatiotemporal_four_dimensional_multigrid_analysis.pdf). *Journal of Geophysical Research: Oceans, 128*(4), e2022JC019386. https://doi.org/10.1029/2022JC019386
