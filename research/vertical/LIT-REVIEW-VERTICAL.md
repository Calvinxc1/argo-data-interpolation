# Vertical Profile Interpolation and Representation: A Literature Review

This review covers methods and findings relevant to the vertical interpolation and representation of individual oceanographic profiles from Argo floats, including operational methods, adaptive spline techniques, sensor error characterization, and data quality frameworks.

---

## Operational Argo Processing Context

Core Argo GDAC processing preserves observed profile levels through quality-control stages. Interpolation is introduced mainly when generating standard-level or gridded derivative products. Real-time and delayed-mode pipelines prioritize QC flags and bias corrections rather than replacing original vertical sampling (Wong et al., 2020). Interpolation methods are therefore most visible in downstream analysis products and toolboxes rather than in the raw profile dissemination layer.

The Argo data management chain proceeds in two stages. Real-time QC is applied within 24 hours of data receipt, performing automated tests for gross errors, impossible values, and spike detection. Delayed-mode QC follows 6 to 12 months after collection, involving expert review, conductivity sensor drift correction via the Owens-Wong-Cabanes (OWC) method, and pressure bias correction. Delayed-mode files carry DATA_MODE = 'D' and provide PARAM_ADJUSTED fields with associated PARAM_ADJUSTED_ERROR values (Wong et al., 2020; Wong, Keeley, Carval and the Argo Data Management Team, 2025).

---

## Vertical Interpolation Methods

### Shape-preserving and thermodynamically constrained methods

Barker and McDougall (2020) introduced Multiply-Rotated PCHIP (MR-PCHIP) and MRST-PCHIP for thermodynamically consistent interpolation of Argo profiles. Their method computes multiple PCHIP interpolants in rotated coordinate systems and averages them to mitigate flat-spot artifacts common to standard PCHIP. A key design choice is using bottle index (observation number) rather than pressure as the independent variable, handling irregular pressure spacing before mapping back to pressure coordinates. MRST-PCHIP jointly treats Absolute Salinity and Conservative Temperature to better preserve water-mass structure in SA-CT space. These methods are implemented in the TEOS-10/GSW toolbox as `gsw_SA_CT_interp` and `gsw_t_interp`.

A central motivation for MRST-PCHIP is the Gibbs ringing problem. Unconstrained cubic interpolating splines produce overshoot at sharp gradient features such as thermoclines and mixed-layer bases. This is a mathematical consequence of the interpolating constraint: the spline must pass exactly through every observation and bends sharply to accommodate transitions, propagating oscillation into adjacent intervals. The magnitude of this overshoot does not diminish with mesh refinement. Barker and McDougall document this failure mode empirically and motivate shape-preserving methods as a response. The mathematical proof that cubic spline overshoot is non-diminishing with refinement is established in Xu et al. (1998, Journal of Computational and Applied Mathematics).

### Earlier operational methods

Linear interpolation is the simplest baseline and remains in use in many legacy products and preliminary analyses. Its principal failure is underestimating gradients at sharp features, leading to systematic bias in derived quantities such as ocean heat content.

The Reiniger-Ross scheme (Reiniger and Ross, 1968) was the operational standard for the World Ocean Database and World Ocean Atlas for decades. At each interpolation point it uses the four nearest observations (two above, two below) to construct a local reference curve, computing two parabolas and taking a weighted average. The intuition is to use more local information than linear interpolation while avoiding the global sensitivity of a full cubic spline. Its critical flaw is in the weighting function, which contains a rational expression whose denominator can approach zero in certain data configurations, causing numerical instability and occasionally producing wildly unrealistic interpolated values. It behaves inconsistently across Argo's depth-varying sampling regimes (Barker and McDougall, 2020).

Akima interpolation (Akima, 1970) is a piecewise cubic method whose slope at each data point is computed using only the five nearest points, with the slope formula down-weighting the influence of points whose adjacent slopes differ dramatically from the local average. The practical effect is much greater resistance to overshoot than natural cubic splines, without the flat-spot tendency of PCHIP. Akima interpolation is not strictly monotonicity-preserving but rarely introduces oscillations between observations. Owens and Wong (2003) used Akima for delayed-mode salinity calibration at WHOI because it handles smooth but occasionally sharp transitions better than natural cubic splines while being simpler to implement than Reiniger-Ross.

### Climate impact of interpolation method choice

Li et al. (2022) demonstrated that the choice of vertical interpolation method materially affects downstream climate estimates. Using linear interpolation rather than MRST-PCHIP yielded ocean heat content warming trends approximately 14% lower over the 1956-2020 historical record, corresponding to approximately 40 Zeta Joules and a thermosteric sea level rise underestimate of 0.55 mm/yr. This establishes vertical interpolation accuracy as a climate-relevant problem with quantified downstream consequences, not merely a numerical detail.

---

## Functional Representation of Individual Profiles

Yarger, Stoev, and Hsing (2022) developed a two-stage spatiotemporal framework for Argo profiles in which each observed profile is first converted into a continuous functional object before spatiotemporal modeling. Their vertical representation step uses B-spline smoothing splines with 200 equispaced knots over [0, 2000] dbar, with GCV for smoothing parameter selection. Smoothing parameters are collapsed into a single global 1D search. A Markovian working within-profile correlation structure is used to stabilize estimation for irregularly sampled profiles.

This is the closest published precedent in the Argo literature to treating vertical profile representation as a continuous function rather than a vector of fixed-level values. The framework treats profiles as continuous curves in depth rather than discrete observations at fixed pressure levels, enabling derivative analysis and natural accommodation of uneven vertical sampling. Their primary contribution is the spatiotemporal kriging system built on top of this representation; the vertical step is infrastructure for that system rather than a contribution in its own right. The full spatiotemporal context and published prediction benchmarks for Yarger et al. (2022) are covered in the companion spatiotemporal literature review.

---

## Adaptive Knot Placement and Spline Representations

### Curvature-adaptive approaches

Li et al. (2005) presented curvature-informed B-spline knot allocation for fitting smooth curves to dense, noisy 3D point clouds from laser scanners of physical objects. Their method smooths discrete curvature with a lowpass digital filter first to separate structural signal from sensor noise, then places knots proportional to the integral of that smoothed curvature, concentrating them in high-curvature regions and leaving flat regions sparse. LSQ spline fitting is used rather than exact interpolation so individual noisy points are averaged rather than honored exactly. The knot count emerges from the data structure rather than being specified in advance. Li et al. (2005) identified four failure modes in prior approaches: failure to separate noise from structure before knot placement, uniform knot spacing regardless of local data complexity, exact interpolation of noisy observations, and requiring the user to specify knot count in advance. Their solution addresses all four simultaneously.

### Error-driven knot refinement

Vitetti et al. (2025) introduced AutoKnots, an error-driven progressive knot refinement method for spline interpolation requiring only a single precision-tolerance parameter. Developed within the NumCosmo astrophysical library, the method progressively inserts knots where the interpolation error exceeds a user-specified threshold, continuing until the tolerance is satisfied everywhere. Although developed for astrophysical applications, the method provides transferable ideas for profile approximation problems with mixed smooth and sharp-gradient regimes.

### Joint knot and smoothing optimization

Müller and Rügamer (2025) examined joint optimization of knot locations and smoothing parameters in adaptive spline fitting, finding that sequential optimization of these two quantities fails to adequately address the inherent complexity of the problem. They advocate for approaches that treat knot placement and smoothing strength as coupled rather than independently tunable parameters. The paper establishes a theoretical basis for why separate tuning of knots and smoothing leads to suboptimal representations.

---

## Sensor Error Characterization and Pressure Bias

### Official Argo sensor uncertainty specifications

The Argo Quality Control Manual for CTD and Trajectory Data (Wong, Keeley, Carval and the Argo Data Management Team, Version 3.9, 2025, DOI: 10.13155/33951) specifies the following uncertainty figures for standard SBE CTD floats (APEX and NAVIS) operating at 0 to 2000 dbar after delayed-mode adjustment:

PRES_ADJUSTED_ERROR = 2.4 dbar (constant, manufacturer's quoted accuracy after drift correction).

TEMP_ADJUSTED_ERROR = 0.002°C (manufacturer's quoted accuracy, stable across float lifetimes, no drift correction needed).

PSAL_ADJUSTED_ERROR = maximum(adjustment uncertainty, 0.01) PSU. The 0.01 PSU floor applies even to salinity records assessed as good and requiring no adjustment, reflecting the practical accuracy limit of the delayed-mode system.

For Deep-Argo floats (SBE-41CP and SBE-61) sampling to 6000 dbar, the pressure error specification is depth-dependent: PRES_ADJUSTED_ERROR = (2.5/6000) × PRES + 2 (Wong et al., 2025, Section 3.10). This formula does not apply to standard 0 to 2000 dbar floats. For RBRargo3|2K CTD floats, the pressure specification is 1 dbar (constant), substantially better than SBE.

The uncertainties of Argo temperature and pressure data have been validated by comparison with high-quality shipboard CTD data and are concluded to be near the manufacturer accuracy specifications (Wong et al., 2023).

### Salinity drift and the OWC method

The primary salinity error source in Argo is conductivity sensor drift from biofouling and cell geometry changes. Approximately 15% of floats deployed after 2015 experienced abrupt salty drift from a conductivity sensor manufacturing change (Wong et al., 2023). The standard correction method is the Owens-Wong-Cabanes (OWC) method, which compares each float's potential temperature-salinity curves against historical climatological curves at nearby locations and depth levels known to be stable in salinity, typically in deep water. Deviations from the climatological relationship are attributed to sensor drift and corrected. The OWC output is PSAL_ADJUSTED with an attached PSAL_ADJUSTED_ERROR. OWC uncertainty estimates are profile-level scalars: a single adjusted error value per profile or per float record segment. The error is not depth-varying within a profile (Wong et al., 2020, 2023).

Wong et al. (2023) note that even after delayed-mode evaluation and adjustment, residual uncertainty can remain in Argo salinity data. The 0.01 PSU expected accuracy is not a metrologically derived value but one grounded in operational experience with the limitations of a delayed-mode system where data quality is assessed against sparse reference data and a changing ocean.

An additional known salinity error source arises when a float ascends through a region of strong temperature gradients, producing a thermal lag error in the conductivity cell measurement. This is corrected as part of delayed-mode processing (Wong et al., 2025, Section 3.5.1).

### Pressure sensor drift in APEX floats

Barker et al. (2011) documented systematic positive pressure sensor drift in APEX floats, which comprised approximately 62% of the Argo array. Three sensor types were affected: Paine, Ametek, and Druck. Drifts exceeding 10 dbar were observed in individual floats, with an array-average correction of approximately -2 dbar for 2003-era data, decreasing to near zero by 2008 due to improved sensor stability. The drift correction method uses the surface pressure reading recorded each time the float surfaces. A stable pressure sensor reads near zero at sea level, so any non-zero surface pressure reading represents the current sensor offset. Subtracting this from subsurface measurements removes the depth-independent drift component.

Barker et al. (2011) showed that uncorrected pressure biases caused overestimation of upper-ocean temperatures and introduced errors into salinity, thermosteric sea level, and ocean heat content estimates. In the global mean, approximately 43% of uncorrectable APEX profiles partially offset the effect of correctable profiles with positive pressure drifts.

### Truncated Negative Pressure Drift (TNPD)

APEX floats with Apf-5, Apf-7, or Apf-8 controller boards were programmed to truncate any negative surface pressure reading to zero before telemetry. This was implemented to turn off the CTD pump as the float neared the surface. The consequence is that negative pressure drift cannot be detected, quantified, or corrected for these floats: the surface pressure reading that would reveal the drift has been masked (Wong et al., 2025, Section 3.3.2). This feature was corrected in Apf-9 and later controller versions.

The TNPD problem was compounded by the discovery that Druck pressure sensors with serial numbers above 2324175 (deployed after approximately October 2006) experienced oil microleak failures at a rate of approximately 30%, causing increasingly negative drift that could reach tens of dbar and eventually render the float inoperable. Pre-2006 Druck sensors had a microleak failure rate of approximately 3%.

Negative pressure offset causes an apparent cold temperature anomaly proportional to the vertical temperature gradient, apparent positive salinity drift detectable by the OWC method, dynamic height anomalies lower than satellite altimetry, and shoaling of isotherm depths over time.

The Argo program addresses TNPD by flagging affected profiles with elevated pressure error values. Profiles from post-2006 Druck sensors with TNPD receive PRES_ADJUSTED_ERROR = 20 dbar. The 20 dbar threshold is physically motivated: a -20 dbar pressure error produces approximately +0.01 PSU apparent salinity error, at which point T/S anomalies become detectable by standard OWC methods. Profiles with T/S anomalies consistent with severe negative drift receive PRES_ADJUSTED_QC = '4' and are flagged as bad data. The Argo program recommends excluding any profile with PRES_ADJUSTED_ERROR = 20 dbar from global change research applications (Barker et al., 2011; Wong et al., 2025).

---

## References

- Akima, H. (1970). A new method of interpolation and smooth curve fitting based on local procedures. *Journal of the ACM, 17*(4), 589-602. https://doi.org/10.1145/321607.321609
- Barker, P. M., Dunn, J. R., Domingues, C. M., & Wijffels, S. E. (2011). Pressure sensor drifts in Argo and their impacts. *Journal of Atmospheric and Oceanic Technology, 28*(8), 1036–1049. https://doi.org/10.1175/2011JTECHO831.1
- Barker, P. M., & McDougall, T. J. (2020). Two interpolation methods using multiply-rotated piecewise cubic Hermite interpolating polynomials. *Journal of Atmospheric and Oceanic Technology, 37*(4), 605–619. https://doi.org/10.1175/JTECH-D-19-0211.1
- Li, W., Xu, S., Zhao, G., & Goh, L. P. (2005). Adaptive knot placement in B-spline curve approximation. *Computer-Aided Design, 37*(8), 791–797. https://doi.org/10.1016/j.cad.2004.09.008
- Li, Y., Church, J. A., McDougall, T. J., & Barker, P. M. (2022). Sensitivity of observationally based estimates of ocean heat content and thermal expansion to vertical interpolation schemes. *Geophysical Research Letters, 49*(24), e2022GL101079. https://doi.org/10.1029/2022GL101079
- Müller, M., & Rügamer, D. (2025). Adaptive spline fitting with joint knot and smoothing parameter selection. *Journal of Computational and Graphical Statistics*. https://doi.org/10.1080/10618600.2025.2450458
- Reiniger, R. F., & Ross, C. K. (1968). A method of interpolation with application to oceanographic data. *Deep Sea Research and Oceanographic Abstracts, 15*(2), 185–193. https://doi.org/10.1016/0011-7471(68)90040-5
- Vitetti, S. D. P., et al. (2025). AutoKnots: Adaptive knot allocation for spline interpolation. *Astronomy and Computing*. https://doi.org/10.1016/j.ascom.2025.100921
- Wong, A. P. S., Gilson, J., & Cabanes, C. (2023). Argo salinity: bias and uncertainty evaluation. *Earth System Science Data, 15*(1), 383–393. https://doi.org/10.5194/essd-15-383-2023
- Wong, A. P. S., Wijffels, S. E., Riser, S. C., et al. (2020). Argo data 1999–2019: Two million temperature-salinity profiles and subsurface velocity observations from a global array of profiling floats. *Frontiers in Marine Science, 7*, 700. https://doi.org/10.3389/fmars.2020.00700
- Wong, A. P. S., Keeley, R., Carval, T., and the Argo Data Management Team (2025). Argo Quality Control Manual for CTD and Trajectory Data. Version 3.9. https://doi.org/10.13155/33951
- Xu, Y., et al. (1998). On the non-diminishing Gibbs phenomenon for interpolating cubic splines. *Journal of Computational and Applied Mathematics*.
- Yarger, D., Stoev, S., & Hsing, T. (2022). A functional-data approach to the Argo data. *The Annals of Applied Statistics, 16*(1), 216–246. https://doi.org/10.1214/21-AOAS1477