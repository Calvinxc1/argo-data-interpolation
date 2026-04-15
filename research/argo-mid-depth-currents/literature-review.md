# Argo Mid-Depth Currents: A Seed Literature Review

## Review Status

This document is a seed literature review created from a planning summary and a small set of cited references already identified for follow-up. It is not yet a full verified topic review.

Claims below are limited to:

- direct source-oriented summaries carried forward from the planning summary
- cautious synthesis tying those references to the current project question
- explicitly labeled follow-up items where bibliographic or full-text verification is still pending

For broader Argo spatio-temporal benchmark context, see [../spatio-temporal/literature-review.md](../spatio-temporal/literature-review.md).

## Trajectory-Based Mid-Depth Velocity Products

The planning summary identifies Zilberman et al. (2023) as the canonical modern Argo parking-depth velocity product. In that framing, the Scripps trajectory-based product supersedes earlier YoMaHa and ANDRO-style compilations as the community reference product for Argo-derived mid-depth currents. The reported scope in the summary is large: approximately 1.3 million velocity estimates across the 800 to 1200 dbar layer, gridded at 1 degree resolution over 2001 to 2020.

If that summary holds under full-text verification, this product is the first source that should anchor any serious work in this repo on Argo-derived current prediction. It defines the benchmark dataset before any custom movement-profile ideas are entertained.

## Error Characterization for Parking-Depth Velocities

The planning summary identifies Xie and Zhu (2008) as the key error-analysis reference for Argo-derived mid-depth velocity estimates. In that summary, the main error sources are:

- float location uncertainty
- surface drift while the float dives and resurfaces
- vertical shear during descent and ascent

The same summary reports that Kalman-filter extrapolation reduced 1000 dbar velocity error to roughly 0.21 cm/s. If confirmed, that result matters because parking-depth velocity uncertainty is already a studied problem with a published decomposition, rather than something this project would need to define from scratch.

Pending local full-text review in this repo, Katsumata and Yoshinari (2010) appear to extend that error discussion from individual-cycle estimation to mapped global parking-level products. In that framing, uncertainty is not only attached to the endpoint estimate of a single float cycle. It also enters through the objective mapping choices used to turn sparse trajectory-derived velocities into a global field. That makes Katsumata and Yoshinari a useful bridge between cycle-level error decomposition and any later attempt to benchmark against a mapped mid-depth current product.

## Ascent and Surface-Position Ambiguity

Official Argo timing documentation now makes explicit that the end of ascent and the reported surface-position sequence are distinct events. In the cycle-timing vocabulary, `AET` marks the time when the float reaches the surface, while `FLT` and `LLT` mark the earliest and latest surface locations gathered during the surface interval, and `TST` marks the start of transmission. The same documentation notes that most floats profile on ascent rather than descent. Separate Argo program guidance adds the operational detail that profile measurements are collected during ascent and only transmitted after the float reaches the surface. For the majority of the modern fleet, the surface interval is typically 15 minutes to 1 hour; older Argos-based floats can remain at the surface for roughly 6 to 12 hours while obtaining positions and completing transmission.

Taken together, those official sources support a narrower current-estimation caution than the general "surface drift matters" statement in the planning summary. The GIS position attached to a profile-oriented Argo data product is not automatically the same thing as the horizontal location of measurements collected during ascent, nor is it automatically the best estimate of the exact surfacing or dive point needed for parking-depth velocity calculations.

The following paper-specific details in this section remain pending full-text review in this repo. Park et al. (2005) treat this as a first-order methodological problem rather than a bookkeeping detail. Their abstract states that subsurface velocity calculation depends on how the float trajectory while on the surface is handled, and it explicitly addresses three linked tasks: accurate determination of surfacing and dive times, extrapolation of surface and dive positions from discrete Argos fixes, and error analysis for the resulting endpoint estimates. The abstract reports endpoint accuracy better than 1.7 km in the East Sea/Sea of Japan and 0.8 km in the Indian Ocean, with individual subsurface velocity uncertainty of order 0.2 cm/s once the full method is applied.

Xie and Zhu (2008) reinforce the same issue at Pacific scale. Their abstract reports that the fix error of Argo trajectory positions ranges from roughly 150 m to 1000 m, and that the main error terms for mid-depth current estimation are location error, surface-drifting error while the float dives and resurfaces, and vertical-shear error during descent and ascent. In that framing, the "position error" relevant to a current product is not just GPS or Argos point accuracy. It is the compound error produced by assigning a subsurface drift endpoint from sparse surface fixes plus timing uncertainty plus unresolved vertical shear.

The practical implication for this repo is therefore specific. If any later modeling step wants to use a reported Argo GIS position as though it were the exact horizontal location of the measured ascent profile or the exact endpoint of the parking-depth drift segment, that step should be treated as an assumption rather than as a direct property of the data product. Zilberman et al. (2023) do not solve this ambiguity away; their abstract instead notes that discrepancies between trajectory-derived velocity products are associated in part with quality-control criteria and selected cycle-time choices, which is consistent with endpoint handling remaining part of the signal chain.

## Model Mismatch at Mid-Depth

The planning summary also flags Cheng et al. (2023) as a strong cautionary reference. The reported result is that only a small fraction of the mid-depth ocean is accurately represented by circulation models, despite combining a large Argo-derived observational set with Lagrangian simulations.

The implication for this project is straightforward: Argo-based current prediction should be treated as an active research problem rather than as a solved engineering capability. Any practical use of a current field would sit on top of an estimate that remains difficult to construct well even in the dedicated circulation literature.

## Reference-Velocity Framing and Thermal Wind

The summary describes a standard physical route for turning Argo-derived mid-depth trajectories into a vertically resolved velocity field: combine thermal-wind shear with an absolute reference velocity measured at parking depth. In that framing, the Argo trajectory product breaks the old level-of-no-motion circularity by supplying an observed absolute velocity near 1000 dbar, which can then anchor upward and downward integration of thermal-wind shear.

That framing is more defensible than a bespoke empirical movement-profile approach because it starts from an established physical method rather than from a new heuristic. It also clarifies why the problem is larger than a small modeling tweak: once a vertically resolved current field is introduced, the project has entered a distinct prediction problem with its own assumptions, diagnostics, and reviewer expectations.

## Bay of Bengal Caveats

The planning summary explicitly warns that Bay of Bengal conditions make naive vertical extrapolation especially risky. The basin combines monsoon-driven surface flows, strong freshwater stratification, a sharp halocline, low-latitude geostrophic weaknesses, boundary-current effects, and energetic eddies. Those are all reasons to doubt that a parking-depth horizontal drift field can be treated as a faithful proxy for the full water-column flow.

That caution is central to the current project decision. The summary supports parking the movement-profile idea for now, not because current structure is irrelevant, but because the simplistic version of the idea is too weakly defended for the basin of interest.

## Data Assimilation as the Operational Direction

The planning summary points to trajectory assimilation work, particularly in the Mediterranean Forecasting System line, as the more operationally credible direction. Pending full-text review in this repo, Nilsson et al. (2011), in the now-identified Mediterranean Forecasting System paper, describe extending the OceanVar scheme to include Argo float trajectories with the goal of constraining intermediate velocity fields at 350 m. The abstract reports that the added trajectory assimilation improved forecasted trajectories by about 15% without degrading the forecast quality of sea-surface height and mass fields. In that framing, assimilating Argo trajectories directly into an ocean state estimate is a more mature path than designing a new heuristic current predictor by hand.

This suggests that the strongest route into Argo-based current prediction may be assimilation-derived or dynamically referenced flow estimation rather than a purely empirical trajectory heuristic.

The same broad point appears to extend to under-ice trajectory recovery, although the exact cited paper metadata still need verification in this repo. The Hansen `ArgoSSM` line, currently traceable here through dissertation and symposium materials rather than a directly checked arXiv record, treats missing float locations under ice as a Bayesian state-space inference problem. That is narrower than the present open-ocean parking-depth current question, but it still reinforces a useful methodological lesson: unresolved float positions are inferential objects with their own uncertainty model, not just missing bookkeeping fields.

## Literature-Derived Gap

The cited current literature, as summarized here, appears to provide:

- benchmark Argo-derived parking-depth velocity products
- published error decompositions for those products
- physically motivated ways to extend mid-depth absolute velocity into vertically resolved geostrophic estimates
- trajectory-assimilation pathways in operational systems

What it does not yet obviously provide is a simple, already validated recipe for producing vertically resolved, basin-reliable current predictions from Argo data alone in a strongly stratified and dynamically complex region. That gap is why this topic should be treated as a dedicated current-prediction problem rather than as a near-solved extension.

## Follow-Up References Requiring Full Verification

The planning summary also identified two additional references worth chasing:

- a Weddell Gyre paper using Argo-derived absolute geostrophic velocities from 50 to 2000 m
- Hansen, D., et al. (2022). *ArgoSSM: A State-space Model of Ocean Floats Under Ice.* The citation was supplied as arXiv:`2210.00118`, but this repo has not yet directly verified the exact preprint metadata or final author list.

The Weddell Gyre reference is likely important to the future current-prediction path, but its full bibliographic details and exact claims still need verification in this repo.

## References

- Cheng, et al. (2023). *Widespread global disparities between modelled and observed mid-depth ocean currents.* Nature Communications. https://doi.org/10.1038/s41467-023-37841-x
- Ollitrault, M., and De Verdiere, A. C. (2014). *The ocean general circulation near 1000 m depth.* Journal of Physical Oceanography, 44, 384 to 409.
- Argo. *Argo cycle timing variables.* https://argo.ucsd.edu/how-do-floats-work/argo-cycle-timing-variables/
- Argo. *How do floats work.* https://argo.ucsd.edu/how-do-floats-work/
- Argo. *Telecommunications systems.* https://argo.ucsd.edu/how-do-floats-work/telecommunications-systems/
- Katsumata, K., and Yoshinari, H. (2010). *Uncertainties in global mapping of Argo drift data at the parking level.* Journal of Oceanography, 66, 553 to 569. https://doi.org/10.1007/s10872-010-0046-4
- Nilsson, J. A. U., Dobricic, S., Pinardi, N., Taillandier, V., and Poulain, P.-M. (2011). *On the assessment of Argo float trajectory assimilation in the Mediterranean Forecasting System.* Ocean Dynamics, 61(10), 1475 to 1490. https://doi.org/10.1007/s10236-011-0437-0
- Park, J. J., Kim, K., King, B. A., and Riser, S. C. (2005). *An advanced method to estimate deep currents from profiling floats.* Journal of Atmospheric and Oceanic Technology, 22(8), 1294 to 1304. https://doi.org/10.1175/JTECH1748.1
- Xie, J., and Zhu, J. (2008). *Estimation of the surface and mid-depth currents from Argo floats in the Pacific and error analysis.* Journal of Marine Systems, 73, 61 to 75. https://doi.org/10.1016/j.jmarsys.2007.09.001
- Zilberman, N. V., Scanderbeg, M., Gray, A. R., and Oke, P. R. (2023). *Scripps Argo trajectory-based velocity product.* Journal of Atmospheric and Oceanic Technology, 40(3), 361 to 374. https://doi.org/10.1175/JTECH-D-22-0065.1
