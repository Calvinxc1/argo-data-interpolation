# Argo Cycle Representation: A Literature Review

Argo profiles are irregularly sampled in pressure, processed through real-time and delayed-mode quality-control pathways, and affected by sensor drift, pressure bias, and varying uncertainty conventions. The literature relevant to representing individual profiles therefore spans Argo data-management practice, profile interpolation methods, functional representations of vertical structure, and adaptive spline methods developed outside oceanography. The organizing question in this review is how these sources characterize the problem of representing a single Argo profile faithfully under those constraints, and what methodological gap remains in the reviewed literature. The review proceeds from Argo processing and sensor-error conventions to interpolation and functional methods, then to adaptive spline work that addresses knot allocation more directly.

---

## Operational Argo Processing Context

Wong et al. (2020, pp. 8-9) describe Argo GDAC distribution as preserving both raw and adjusted profile values through the real-time and delayed-mode pathways. They also describe a vertical interpolation step in the GDAC-generated S-profile files, where CTD and biogeochemical variables with different vertical sampling schemes are aligned. Their discussion centers on quality control, adjustment, uncertainty metadata, and distribution formats that preserve both raw and adjusted values.

The Argo data management chain proceeds in two stages. Real-time QC is applied within 24 hours of data receipt, performing automated tests for gross errors, impossible values, and spike detection. Delayed-mode QC typically begins about 12 months after collection, involving expert review, conductivity sensor drift correction via the Owens-Wong-Cabanes (OWC) method, and pressure bias correction; delayed-mode salinity products are often available about 12 to 18 months after the raw measurements are collected. Delayed-mode processing retains raw data and adds adjusted values and associated uncertainty estimates in the Argo files (Wong et al., 2020, p. 8; Wong et al., 2023, p. 3; Wong, Keeley, Carval and the Argo Data Management Team, 2025, pp. 55-56).

---

## Sensor Error Characterization and Pressure Bias

### Official Argo sensor uncertainty specifications

The Argo Quality Control Manual for CTD and Trajectory Data (Wong, Keeley, Carval and the Argo Data Management Team, Version 3.9, 2025, DOI: 10.13155/33951) specifies the following uncertainty figures for standard SBE CTD floats (APEX and NAVIS) operating at 0 to 2000 dbar after delayed-mode adjustment:

PRES_ADJUSTED_ERROR = 2.4 dbar (constant, manufacturer's quoted accuracy after drift correction) (Wong et al., 2025, pp. 43, 47).

TEMP_ADJUSTED_ERROR = 0.002°C (manufacturer's quoted accuracy, stable across float lifetimes, no drift correction needed) (Wong et al., 2025, pp. 50, 84).

PSAL_ADJUSTED_ERROR = maximum(adjustment uncertainty, 0.01) PSU. The 0.01 PSU floor applies even to salinity records assessed as good and requiring no adjustment, reflecting the practical accuracy limit of the delayed-mode system (Wong et al., 2025, pp. 55-56, 84).

For Deep-Argo floats (SBE-41CP and SBE-61) sampling to 6000 dbar, the pressure error specification is depth-dependent: PRES_ADJUSTED_ERROR = (2.5/6000) × PRES + 2 (Wong et al., 2025, pp. 33, 77). This formula does not apply to standard 0 to 2000 dbar floats. For RBRargo3|2K CTD floats, the delayed-mode pressure specification is 1 dbar (constant) (Wong et al., 2025, p. 84).

The uncertainties of Argo temperature and pressure data have been validated by comparison with high-quality shipboard CTD data and are concluded to be near the manufacturer accuracy specifications (Wong et al., 2023, p. 2).

### Salinity drift and the OWC method

The primary salinity error source in Argo is conductivity sensor drift. Wong et al. (2023, p. 3) show that adjustable salty drift increased after 2015 and peaked in 2017-2018 at about 17% of annual profiles, associated with a CTD manufacturing problem. The standard correction method is the Owens-Wong-Cabanes (OWC) method, which compares float salinity data against nearby reference data on selected pressure or potential-temperature surfaces in order to diagnose and correct sensor drift (Wong et al., 2023, pp. 2-3). In Argo data files, delayed-mode salinity adjustments are distributed as `PSAL_ADJUSTED` with associated `PSAL_ADJUSTED_ERROR` values assigned through the delayed-mode QC procedures (Wong, Keeley, Carval and the Argo Data Management Team, 2025, pp. 55-56, 84).

Wong et al. (2023, p. 9) note that even after delayed-mode evaluation and adjustment, residual uncertainty can remain in Argo salinity data. The 0.01 PSU expected accuracy is not a metrologically derived value but one grounded in operational experience with the limitations of a delayed-mode system where data quality is assessed against sparse reference data and a changing ocean (Wong et al., 2023, p. 9). In the reviewed Argo sources, this salinity uncertainty is assigned through delayed-mode QC procedures as a profile- or record-segment quantity rather than as a depth-varying within-profile uncertainty model.

An additional known salinity error source arises when a float ascends through a region of strong temperature gradients, producing a thermal lag error in the conductivity cell measurement. This is corrected as part of delayed-mode processing (Wong et al., 2023, p. 3; Wong et al., 2025, p. 51).

### Pressure sensor drift in APEX floats

Barker et al. (2011, pp. 1-3) documented systematic pressure sensor drift in APEX floats, which comprised approximately 62% of the Argo array. Three sensor types were affected: Paine, Ametek, and Druck. Drifts exceeding 10 dbar were observed in individual floats. The drift correction method uses the surface pressure reading recorded each time the float surfaces. A stable pressure sensor reads near zero at sea level, so any non-zero surface pressure reading represents the current sensor offset. Subtracting this from subsurface measurements removes the depth-independent drift component.

Barker et al. (2011, pp. 1, 8-12) showed that uncorrected pressure biases caused overestimation of upper-ocean temperatures and introduced errors into salinity, thermosteric sea level, and ocean heat content estimates. In the global mean, approximately 43% of uncorrectable APEX profiles partially offset the effect of correctable profiles with positive pressure drifts. Taken together with the QC manual, these sources distinguish systematic pressure drift, which is diagnosed and corrected from surface-pressure behavior, from the residual measurement uncertainty cited for delayed-mode pressure values after correction.

### Truncated Negative Pressure Drift (TNPD)

APEX floats with Apf-5, Apf-7, or Apf-8 controller boards were programmed to truncate any negative surface pressure reading to zero before telemetry. This was implemented to turn off the CTD pump as the float neared the surface. The consequence is that negative pressure drift cannot be detected, quantified, or corrected for these floats: the surface pressure reading that would reveal the drift has been masked, and this feature was corrected in Apf-9 and later controller versions (Wong et al., 2025, p. 44).

The TNPD problem was compounded by the discovery that Druck pressure sensors with serial numbers above 2324175 (deployed after approximately October 2006) experienced oil microleak failures at a rate of approximately 30%, causing increasingly negative drift that could reach tens of dbar and eventually render the float inoperable. Pre-2006 Druck sensors had a microleak failure rate of approximately 3% (Wong et al., 2025, pp. 46-47).

Negative pressure offset causes an apparent cold temperature anomaly proportional to the vertical temperature gradient, apparent positive salinity drift detectable by the OWC method, dynamic height anomalies lower than satellite altimetry, and shoaling of isotherm depths over time (Wong et al., 2025, p. 46).

The Argo program addresses TNPD by flagging affected profiles with elevated pressure error values. Profiles from post-2006 Druck sensors with TNPD may receive PRES_ADJUSTED_ERROR = 20 dbar when the data are still considered usable but suspicious. The 20 dbar threshold is physically motivated: a -20 dbar pressure error produces approximately +0.01 PSU apparent salinity error, at which point T/S anomalies become detectable by standard OWC methods. When T/S anomalies indicate severe negative drift, the manual sets PRES_ADJUSTED_QC, TEMP_ADJUSTED_QC, and PSAL_ADJUSTED_QC to '4', with adjusted values filled as bad data (Wong et al., 2025, pp. 47-48). Barker et al. (2011, pp. 4, 8, 12) excluded TNPD-related uncorrectable profiles from ocean heat content and decadal-change analyses.

These operational uncertainty and QC conventions define the conditions under which vertical interpolation and representation methods must operate.

---

## Vertical Interpolation Methods

Against that measurement and QC backdrop, the interpolation literature addresses how to reconstruct values between observed levels without introducing unrealistic structure.

### Shape-preserving and thermodynamically constrained methods

Barker and McDougall (2020, pp. 1-2, 4-7, 14-15) introduced Multiply-Rotated PCHIP (MR-PCHIP) and MRST-PCHIP for thermodynamically consistent interpolation of Argo profiles. Their method computes multiple PCHIP interpolants in rotated coordinate systems and averages them to mitigate flat-spot artifacts common to standard PCHIP. A key design choice is using bottle index (observation number) rather than pressure as the independent variable, handling irregular pressure spacing before mapping back to pressure coordinates. MRST-PCHIP jointly treats Absolute Salinity and Conservative Temperature to better preserve water-mass structure in SA-CT space. Within the broader TEOS-10/GSW ecosystem, these interpolation routines are described in connection with `gsw_SA_CT_interp` and `gsw_t_interp` in the Barker and McDougall presentation of the method.

For this project's implementation context, however, the official GSW-Python documentation exposes `interp_method='mrst'` only on `geo_strf_dyn_height()` and `geo_strf_steric_height()`. The same documentation for `sa_ct_interp()` and `tracer_ct_interp()` does not expose an `interp_method` argument, so the Python binding does not presently document MRST-PCHIP as a standalone general-purpose vertical-profile interpolator (GSW-Python documentation, `geostrophy` and `all functions` pages). This is an implementation-scope observation about the Python interface, not a limitation claimed by Barker and McDougall (2020) about the method itself.

A central motivation for MRST-PCHIP is the Gibbs ringing problem. Unconstrained cubic interpolating splines produce overshoot at sharp gradient features such as thermoclines and mixed-layer bases. Barker and McDougall (2020, pp. 3, 14) document this failure mode empirically and motivate shape-preserving methods as a response. For discontinuous functions, Zhang and Martin (1997, pp. 359-360, 364) show that complete cubic spline interpolation on uniform meshes exhibits Gibbs-type oscillation near the discontinuity and that the maximum overshoot does not decrease with mesh refinement. That result is not a proof for ocean thermoclines specifically, but within this source set it is the clearest mathematical support for the spline-ringing concern discussed in the oceanographic interpolation literature.

### Earlier operational methods

Linear interpolation is the simplest baseline. In the context examined by Li et al. (2022, pp. 1, 8), it underestimates sharp vertical gradients relative to MRST-PCHIP, leading to systematic bias in derived quantities such as ocean heat content.

The Reiniger-Ross scheme (Reiniger and Ross, 1968, pp. 185-188) uses four nearby observations, two above and two below the interpolation depth, to construct a local reference curve and combine overlapping parabolic interpolants with weights designed to reduce overshoot. Barker and McDougall (2020, p. 2) identify failure cases for RR68, including unrealistic excursions under some profile configurations.

Akima interpolation (Akima, 1970, pp. 2-5) is a piecewise cubic method in which the slope at each data point is determined locally from five nearby points, and each interval is then represented by a cubic polynomial fixed by the endpoint values and endpoint slopes. Akima motivates the method as a local, visually natural alternative to other smooth interpolation procedures. Wong, Johnson, and Owens (2003, p. 2) used a shape-preserving spline, specifically Akima (1970), to vertically interpolate historical bottle salinity data onto standard potential-temperature surfaces when constructing the θ-S climatology used for delayed-mode calibration.

### Climate impact of interpolation method choice

Li et al. (2022, pp. 1, 4, 7-8) compared multiple vertical interpolation methods for historical ocean heat content estimation. Using linear interpolation rather than MRST-PCHIP yielded ocean heat content warming trends approximately 14% lower over the 1956-2020 historical record, corresponding to approximately 40 Zeta Joules and a thermosteric sea level rise underestimate of 0.55 mm/yr.

---

## Functional Representation of Individual Profiles

Where the interpolation papers focus on reconstructing values between observed profile levels, Yarger, Stoev, and Hsing (2022, pp. 1-4, 11-12) reformulate Argo profiles as function-valued data over pressure.

Yarger, Stoev, and Hsing (2022, pp. 11-12) developed a two-stage spatiotemporal framework for Argo profiles in which each observed profile is first converted into a continuous functional object before spatiotemporal modeling. Their vertical representation step uses penalized cubic B-spline smoothing with 200 equispaced knots over [0, 2000] dbar, with GCV for smoothing-parameter selection. Smoothing parameters are reduced to a single one-dimensional search, and a Markovian working within-profile correlation structure is used to stabilize estimation for irregularly sampled profiles. In this reviewed source set, this is the most direct treatment of Argo profiles as continuous functions rather than only as values on a standard pressure grid.

Yarger et al. position this functional approach against pressure-level methods that first linearly interpolate each profile onto fixed pressure levels. They argue that the functional treatment avoids interpolation error for sparsely sampled profiles, uses all available measurements from densely sampled profiles, and makes derivative and integral estimates available directly over pressure (Yarger et al., 2022, pp. 216-218). Their vertical smoother is therefore part of a broader spatiotemporal functional-kriging framework that targets prediction and uncertainty over space, time, and pressure rather than a standalone stored representation for each profile. The design is equispaced and globally tuned rather than profile-adaptive: knot placement is fixed over pressure, the smoothing search is simplified by holding parameter ratios fixed, and the conclusion identifies adaptive neighborhood selection and pressure-varying scale behavior as future directions (Yarger et al., 2022, pp. 226-227, 235-236, 241).

In validation, Yarger et al. report good empirical interval and band coverage overall, while noting that pointwise coverage by pressure is typically weaker over 20 to 200 dbar because of more complex near-surface processes (Yarger et al., 2022, p. 238). That validation establishes the framework as a serious functional treatment of Argo profiles, but the pressure-adaptivity limitations identified by the authors remain relevant to the single-profile representation problem considered here.

---

## Additional Adaptive Spline Methods

The Argo-specific sources above do not treat adaptive knot allocation in detail. A separate spline literature addresses that question more directly through knot placement, precision-driven refinement, and joint knot-smoothing optimization.

Li et al. (2005, pp. 791-794) presented an adaptive knot-placement method for B-spline curve approximation of dense, noisy 3D point-cloud data from laser scans rather than from oceanographic profiles. They identify four shortcomings in earlier methods: failure to separate noise from structure before knot placement, knot spacing that does not track local geometric complexity, exact interpolation of noisy observations, and the need for the user to specify knot count in advance. Their method smooths discrete curvature with a lowpass digital filter, places knots according to the integral of the smoothed curvature, and fits the curve by least-squares spline approximation rather than exact interpolation.

Vitenti et al. (2025, pp. 1, 4-5) introduced AutoKnots, an adaptive knot-allocation method for spline interpolation developed in the NumCosmo scientific-computing library for cosmology and related astrophysical applications. In that method, the user-defined precision target is an interpolation-error tolerance, and the algorithm refines the spline by adding sample points in regions where the estimated error exceeds that threshold.

Thielmann, Kneib, and Säfken (2025, pp. 1398-1399, 1401) studied adaptive spline regression with joint optimization of knot locations and smoothing parameters. They argue that sequential selection can perform poorly because the two decisions are interdependent, and they propose a particle-swarm-based optimization strategy.

---

## Synthesis and Gap

Taken together, the reviewed literature defines a layered representation problem. Argo operational sources describe a data stream in which raw and adjusted profiles are preserved, but interpreted through sensor-specific uncertainty conventions, salinity-drift correction, pressure-bias handling, and QC decisions. Oceanographic interpolation papers address how to reconstruct values between irregularly spaced observations while limiting overshoot and preserving physically plausible structure. Yarger et al. extend the problem from interpolation to continuous functional representation, but do so within a larger spatiotemporal prediction framework, while the additional adaptive-spline papers treat knot allocation outside the Argo setting.

Within this source set, the remaining gap is a standalone method for representing individual Argo profiles that combines irregular-sampling-aware vertical approximation with source-calibrated profile-level uncertainty treatment, since the reviewed sources either focus on interpolation between observed levels, embed vertical representation and uncertainty inside a broader spatiotemporal model, or develop adaptive spline mechanisms outside the Argo literature.

---

## References

**Review status note**: References with linked local files below were checked against local full-text copies. One exception is Vitenti et al. (2025), where the local file is an author-style preprint carrying the expected title, authors, and DOI but not the final publisher-formatted journal front matter.

- Akima, H. (1970). [A new method of interpolation and smooth curve fitting based on local procedures](sources/akima-1970-smooth_curve_fitting.pdf). *Journal of the ACM, 17*(4), 589-602. https://doi.org/10.1145/321607.321609
- Barker, P. M., Dunn, J. R., Domingues, C. M., & Wijffels, S. E. (2011). [Pressure sensor drifts in Argo and their impacts](sources/barker-2011-pressure_sensor_drifts_in_argo.pdf). *Journal of Atmospheric and Oceanic Technology, 28*(8), 1036–1049. https://doi.org/10.1175/2011JTECHO831.1
- Barker, P. M., & McDougall, T. J. (2020). [Two interpolation methods using multiply-rotated piecewise cubic Hermite interpolating polynomials](sources/barker-2020-two_interpolation_methods.pdf). *Journal of Atmospheric and Oceanic Technology, 37*(4), 605–619. https://doi.org/10.1175/JTECH-D-19-0211.1
- GSW-Python documentation. [All functions](https://teos-10.github.io/GSW-Python/gsw_flat.html).
- GSW-Python documentation. [Geostrophy](https://teos-10.github.io/GSW-Python/geostrophy.html).
- Li, W., Xu, S., Zhao, G., & Goh, L. P. (2005). [Adaptive knot placement in B-spline curve approximation](sources/li-2005-adaptive_knot_placement_in_b_spline_curve_approximation.pdf). *Computer-Aided Design, 37*(8), 791–797. https://doi.org/10.1016/j.cad.2004.09.008
- Li, Y., Church, J. A., McDougall, T. J., & Barker, P. M. (2022). [Sensitivity of observationally based estimates of ocean heat content and thermal expansion to vertical interpolation schemes](sources/li-2022-ocean_heat_content_interpolation_sensitivity.pdf). *Geophysical Research Letters, 49*(24), e2022GL101079. https://doi.org/10.1029/2022GL101079
- Reiniger, R. F., & Ross, C. K. (1968). [A method of interpolation with application to oceanographic data](sources/reiniger-1968-method_of_interpolation_oceanographic_data.pdf). *Deep Sea Research and Oceanographic Abstracts, 15*(2), 185–193. https://doi.org/10.1016/0011-7471(68)90040-5
- Thielmann, A., Kneib, T., & Säfken, B. (2025). [Enhancing adaptive spline regression: An evolutionary approach to optimal knot placement and smoothing parameter selection](sources/thielmann-2025-adaptive_spline_regression.pdf). *Journal of Computational and Graphical Statistics, 34*(4), 1397–1409. https://doi.org/10.1080/10618600.2025.2450458
- Vitenti, S. D. P., de Simoni, F., Penna-Lima, M., & Barroso, E. J. (2025). [AutoKnots: Adaptive knot allocation for spline interpolation](sources/vitenti-2025-autoknots.pdf). *Astronomy and Computing*. https://doi.org/10.1016/j.ascom.2025.100970. Local copy is an author-style preprint rather than the final publisher PDF.
- Wong, A. P. S., Johnson, G. C., & Owens, W. B. (2003). [Delayed-mode calibration of autonomous CTD profiling float salinity data by θ-S climatology](sources/wong-2003-delayed_mode_calibration_of_ctd.pdf). *Journal of Atmospheric and Oceanic Technology, 20*(2), 308–318. https://doi.org/10.1175/1520-0426(2003)020<0308:DMCOAC>2.0.CO;2
- Wong, A. P. S., Wijffels, S. E., Riser, S. C., et al. (2020). [Argo data 1999–2019: Two million temperature-salinity profiles and subsurface velocity observations from a global array of profiling floats](sources/wong-2020-argo_data_1999_2019.pdf). *Frontiers in Marine Science, 7*, 700. https://doi.org/10.3389/fmars.2020.00700
- Wong, A. P. S., Gilson, J., & Cabanes, C. (2023). [Argo salinity: bias and uncertainty evaluation](sources/wong-2023-argo_salinity.pdf). *Earth System Science Data, 15*(1), 383–393. https://doi.org/10.5194/essd-15-383-2023
- Wong, A. P. S., Keeley, R., Carval, T., and the Argo Data Management Team (2025). [Argo Quality Control Manual for CTD and Trajectory Data](sources/wong-2025-argo_qc_manual.pdf). Version 3.9. https://doi.org/10.13155/33951
- Yarger, D., Stoev, S., & Hsing, T. (2022). [A functional-data approach to the Argo data](sources/yarger-2022-functional_data_approach_to_argo.pdf). *The Annals of Applied Statistics, 16*(1), 216–246. https://doi.org/10.1214/21-AOAS1477
- Zhang, Z. M., & Martin, C. F. (1997). [Convergence and Gibbs' phenomenon in cubic spline interpolation of discontinuous functions](sources/zhang-1997-convergence_and_gibbs_in_spline_interpolation.pdf). *Journal of Computational and Applied Mathematics, 87*(2), 359–371. https://doi.org/10.1016/S0377-0427(97)00199-4
