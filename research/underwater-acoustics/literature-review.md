# Sound Speed Estimation From Argo Float Data: A Literature Review

## Review Status

This file is the canonical literature review for the `underwater-acoustics` topic.

The present draft was constructed from the research compilation that had been accumulated in [README.md](README.md). Only Jana et al. (2022) currently has a local full-text copy in [sources/](sources/). The remaining citations and the synthesis built on them are therefore **pending full-text review and bibliography normalization**. No page numbers are included yet. Until the source copies are collected and checked, treat this document as a structured literature map with preserved inline references, not as a fully verified final review.

## Overview

The current citation set suggests that **Argo float data have become a primary in-situ foundation for large-scale ocean sound-speed estimation**, supporting work that ranges from climatological mapping to acoustic propagation studies, sound-channel diagnostics, machine-learning prediction, and operational ocean forecasting. Across that literature, seven themes recur:

1. sound-speed equations and thermodynamic standards
2. Argo-derived sound-speed climatologies and regional variability studies
3. vertical interpolation choices and their under-reported consequences
4. uncertainty quantification from sensors through mapped products
5. acoustic propagation, tomography, and operational applications
6. machine-learning and statistical profile modeling
7. the expanding observational scope of the Argo program itself

The citation set also points to a sharp methodological gap: **the interpolation step between native Argo profiles and derived sound-speed profiles is rarely documented explicitly**, even though neighboring literatures have already shown that interpolation choice can materially bias derived ocean-state quantities.

## Sound Speed Equations: From UNESCO to TEOS-10

The current source list traces a well-defined lineage of seawater sound-speed equations. Wilson (1960) appears as the earliest widely cited empirical formulation. Del Grosso (1974, DOI: `10.1121/1.1903388`) and Chen and Millero (1977, DOI: `10.1121/1.381646`) superseded that early work, with the Chen-Millero formulation later codified as the UNESCO / EOS-80 standard by Fofonoff and Millard (1983). The draft source set also includes the key correction and comparison papers around that standard: Spiesberger and Metzger (1991a, 1991b), Dushaw et al. (1993, DOI: `10.1121/1.405660`), Spiesberger (1993), Millero and Li (1994, DOI: `10.1121/1.409844`), Wong and Zhu (1995, DOI: `10.1121/1.413048`), and Meinen and Watts (1997, DOI: `10.1121/1.419655`). Taken together, those citations indicate that Del Grosso remained competitive, and often preferable, for deep-ocean acoustic use even after UNESCO adoption.

The same citation set points to a parallel family of simplified equations used in practice: Mackenzie (1981, DOI: `10.1121/1.386920`), Coppens (1981), Leroy, Robinson, and Goldsmith (2008, DOI: `10.1121/1.2988296`), Pike and Beiboer (1993), and Brewer et al. (2015, DOI: `10.1016/j.marchem.2015.09.009`). These references suggest an enduring tradeoff between computational simplicity, physical realism, and global validity range.

The modern thermodynamic standard is TEOS-10, anchored in IOC, SCOR, and IAPSO (2010), Feistel (2003, 2008, DOI: `10.1016/j.dsr.2008.07.004`), Feistel et al. (2010), Pawlowicz et al. (2012), McDougall et al. (2003), and Roquet et al. (2015, DOI: `10.1016/j.ocemod.2015.04.002`). The draft source list indicates that TEOS-10's main advantage is thermodynamic consistency across seawater properties, with the Roquet et al. polynomial approximation becoming the efficient implementation path in model and toolbox settings. Allen et al. (2017, DOI: `10.1002/lom3.10203`) and Allen et al. (2025, DOI: `10.1002/lom3.10715`) extend that framework into reverse sound-speed / salinity calculations for instruments.

The main implication for this topic is straightforward: the literature already contains both the legacy UNESCO / Del Grosso lineage and the TEOS-10 path. That gives this project a clean baseline-versus-upgrade framing rather than a need to invent a new equation choice.

## Argo-Derived Sound Speed Climatologies and Regional Variability

The draft source set suggests that Argo-enabled sound-speed studies now span global climatology, climate-change projections, basin-scale regional diagnostics, and sound-channel classification.

At the global scale, Chu and Fan (2024, DOI: `10.1038/s41597-024-04074-6`) appear to provide a global climatological dataset of acoustic parameters derived from WOA 2023. Affatati, Scaini, and Salon (2022, DOI: `10.1029/2021EF002099`) and Possenti et al. (2023, DOI: `10.7717/peerj.16208`) extend the topic into climate-change impact assessment, linking warming and circulation change to projected sound-speed change and ducting structure.

At the regional scale, the current citation set is especially rich. Jana et al. (2022, DOI: `10.1109/OCEANSChennai45887.2022.9775509`) anchor the Bay of Bengal workflow that this repository is already replicating. The Arabian Sea literature in the draft list includes Udaya Bhaskar, Swain, and Ravichandran (2008, DOI: `10.1007/BF03020695`), Udaya Bhaskar et al. (2012), Udaya Bhaskar and Swain (2016), and Srinivasu et al. (2024, DOI: `10.1029/2023EA003497`), all of which point to strong links among mixed-layer structure, barrier layers, seasonal forcing, and sonic-layer depth. Additional regional studies in the source set include Zhang et al. (2023, DOI: `10.1007/s10872-023-00701-9`) and Chen et al. (2020, DOI: `10.1016/j.apacoust.2020.107478`) for the Northwest Pacific and Kuroshio Extension, Salon et al. (2003) for the Mediterranean, Armansyah, Sukoco, and Pranowo (2018) for the Banda Sea, and a 2024 *Remote Sensing* paper on South China Sea eddy effects.

The citation inventory also indicates a sub-literature on SOFAR and deep sound channels, including Swaminathan and Bhaskaran (2009) plus earlier Indian Ocean work by Prasanna Kumar and Somayajulu. Separate classification-oriented studies appear in He et al. (2024), Hjelmervik, Jensen, and Østenstad (2012, DOI: `10.1007/s10236-011-0499-z`), Hjelmervik and Hjelmervik (2013, DOI: `10.1007/s10236-013-0623-3`), Xu et al. (2009), Mandelberg and Frizzell-Makowski (2000), and a 2023 *Frontiers in Marine Science* paper (DOI: `10.3389/fmars.2023.1130061`). Penupothu (2025, DOI: `10.21227/61qc-z803`) appears to offer an ML-ready Indian Ocean SSP time series dataset.

For this repository, the main value of this body of work is that it shows Jana et al. is not an isolated case. It sits inside a broader Argo-enabled acoustics literature where regional structure, sound-channel metrics, and downstream propagation relevance are already established.

## Vertical Interpolation Methods Remain Under-Reported

The most important process gap in the current citation set is vertical interpolation. The literature draft indicates that many Argo-to-sound-speed studies report gridding to standard depth levels but **do not specify the interpolation algorithm used**.

The classical reference in the source list is Reiniger and Ross (1968, DOI: `10.1016/0011-7471(68)90040-5`), whose weighted parabolic method appears repeatedly in ocean heat content and gridded-product workflows. Cheng and Zhu (2014, DOI: `10.1175/JTECH-D-13-00220.1`) provide a particularly important comparison, suggesting that linear interpolation and spline interpolation can each introduce systematic temperature biases relative to Reiniger-Ross in heat-content calculations. Barker and McDougall (2020, DOI: `10.1175/JTECH-D-19-0211.1`) appear to establish the current state of the art through MR-PCHIP and MRST-PCHIP, with direct relevance to Argo T/S profile interpolation and with implementations carried into GSW. The draft source set also includes Fritsch and Carlson (1980) for the original PCHIP algorithm, Akima (1970) for Akima splines, Katsura (2021, DOI: `10.1029/2020JC016591`), Li et al. (2022, DOI: `10.1029/2022GL101079`), North and Livingstone (2013), and Yu et al. (2022, DOI: `10.3389/fmars.2022.1030980`).

Li et al. (2022) are especially consequential in this draft literature map because they suggest that **linear interpolation can bias a major derived climate metric by roughly 14%** relative to more advanced schemes. That finding is not about sound speed directly, but it strongly motivates asking the analogous question for derived acoustic structure from Argo profiles.

The gridded-product references in the draft set reinforce the point that interpolation choices are heterogeneous: Roemmich and Gilson (2009, DOI: `10.1016/j.pocean.2009.03.004`), Gaillard et al. (2016, DOI: `10.1175/JCLI-D-15-0028.1`), Li et al. (2017, DOI: `10.1002/2016JC012285`), Good, Martin, and Rayner (2013, DOI: `10.1002/2013JC009067`), Schmidtko, Johnson, and Lyman (2013, DOI: `10.1002/jgrc.20122`), Ridgway, Dunn, and Wilkin (2002), Dunn and Ridgway (2002), Gouretski (2018, DOI: `10.5194/os-14-1127-2018`), the 2022 GDCSM-Argo product, Cheng et al. (2024, DOI: `10.5194/essd-16-3517-2024`), and Zhou et al. (2023, DOI: `10.1029/2022JC019386`) all imply different depth-level or surface frameworks. Wong et al. (2020, DOI: `10.3389/fmars.2020.00700`) are the key programmatic reference in this context because Argo itself distributes native-level profiles without prescribing the interpolation method.

This is the clearest literature-backed opening for the current project: a per-profile interpolation study for derived sound speed is justified by adjacent evidence, but appears not to have been done explicitly in the draft source set.

## Uncertainty Quantification: Sensor Precision Versus Mapping Error

The uncertainty story in the current citation set separates cleanly into sensor-level precision, delayed-mode correction and QC, equation uncertainty, and mapped-product discrepancy.

Wong et al. (2020, DOI: `10.3389/fmars.2020.00700`) and Kobayashi et al. (2019, DOI: `10.1186/s40645-019-0310-1`) anchor the sensor side of the draft review. They suggest temperature precision around ±0.002°C, conductivity or salinity precision on the order of 10^-3, and field pressure uncertainty of a few dbar for standard Argo CTDs. Wong, Gilson, and Cabanes (2023, DOI: `10.5194/essd-15-383-2023`) and Fujii et al. (2024, DOI: `10.3389/fmars.2024.1496409`) extend that picture into delayed-mode salinity drift, gray-listing, and system-level impacts of sensor bias. The delayed-mode QC method references in the citation set are Wong, Johnson, and Owens (2003), Owens and Wong (2009), and Cabanes, Thierry, and Lagadec (2016).

The draft source inventory also points to a relatively mature sound-speed error-propagation basis. Allen et al. (2017, 2025) provide equation-side uncertainty context, while Grekov, Grekov, and Sychov (2021, DOI: `10.1016/j.measurement.2021.109073`) appear to offer the most rigorous propagation treatment under the GUM framework. The sensitivity picture in the draft notes is familiar: temperature dominates, salinity is secondary, and pressure contributes more strongly at depth. The resulting Argo sensor-level sound-speed uncertainty is summarized in the draft as being on the order of **0.04 m/s**.

That low instrument-level uncertainty contrasts sharply with product-level spread. Zhou et al. (2023), Liu et al. (2024, DOI: `10.1029/2023JC020871`), Good et al. (2013), and Kuusela and Stein (2018, DOI: `10.1098/rspa.2018.0400`) together suggest that gridded T/S products diverge enough to imply sound-speed discrepancies of several m/s, while formal uncertainty fields remain sparse and inconsistently calibrated.

The project-level implication is important: the literature already provides the ingredients for a sensor-to-sound-speed uncertainty chain, but the interpolation step still appears weakly integrated into that chain for individual Argo profiles.

## Acoustic Applications Increasingly Depend on Argo

The citation set indicates that Argo-derived sound-speed information is now tightly coupled to both research and operational acoustics.

Operational forecasting and naval acoustics appear throughout the draft references: HYCOM/NCODA via Chassignet et al. (2009), Cummings (2005), and Cummings and Smedstad (2013); GDEM via Carnes (2009) and Teague, Carron, and Hogan (1990); acoustic modeling links such as Chu, Haeger, et al. (2002); broader coordinated prediction systems through Le Traon et al. (2019), Lellouche et al. (2018), Jean-Michel et al. (2021), Bell et al. (2009), Tonani et al. (2015), and Chassignet et al. (2020). The draft source set also points to Arctic and East Asian operationally motivated work via NATO CMRE and the Korean Acoustical Society (2021).

Ocean acoustic tomography appears as an especially revealing comparison system in the draft literature. Dushaw et al. (2009, DOI: `10.1029/2008JC005124`), Dushaw (2019, DOI: `10.1175/JTECH-D-18-0082.1`), Dushaw (2022, DOI: `10.16993/tellusa.39`), Woolfe et al. (2015, DOI: `10.1002/2015GL063438`), and Munk, Worcester, and Wunsch (1995) all suggest that Argo and tomography each capture important but incomplete pieces of the same thermal structure, and that line-integrated acoustic constraints can reveal deficits that profile-based observations alone miss.

Sensitivity and propagation-focused studies in the draft inventory include Chen et al. (2017), Chen et al. (2018), a 2024 *Frontiers in Marine Science* convergence-zone prediction paper (DOI: `10.3389/fmars.2024.1364884`), a 2025 eddy-parameterized propagation-loss paper (DOI: `10.3389/fmars.2025.1588066`), and a 2025 *JMSE* convergence-zone paper. These citations suggest that Argo-derived SSP variability is already being treated as acoustically consequential in propagation contexts.

The source list also hints at an emerging direct instrumentation bridge between Argo and passive acoustics, via Nystuen et al. (~2014) and Bozzano et al. (2026, DOI: `10.5194/os-22-101-2026`).

For this repository, that means a deterministic Argo-to-sound-speed replication is already operationally legible. The remaining contribution space is not to prove sound speed matters for acoustics, but to quantify how interpolation and uncertainty matter once sound speed is already in the loop.

## Machine Learning and Statistical Methods Advance Rapidly

The current bibliography suggests a fast-moving statistical and machine-learning literature around Argo-derived profile prediction, spatiotemporal interpolation, and uncertainty-aware mapping.

On the probabilistic-statistical side, the most important references in the draft list appear to be Kuusela and Stein (2018, DOI: `10.1098/rspa.2018.0400`), Park, Kuusela, Giglio, and Gray (2023, DOI: `10.1214/22-AOAS1679`), Cao et al. (2025), and Su et al. (2023, DOI: `10.3389/fmars.2023.1121334`). These works suggest that Gaussian-process-based approaches already provide a sophisticated uncertainty language for nonstationary, heteroskedastic ocean fields.

For neural-network uncertainty precedents, the draft source set highlights CANYON (Sauzède et al., 2017, DOI: `10.3389/fmars.2017.00128`), CANYON-B (Bittig et al., 2018, DOI: `10.3389/fmars.2018.00328`), ESPER (Carter et al., 2021, DOI: `10.1002/lom3.10461`), CANYON-MED (Fourrier et al., 2020), GOM-NNpH (Osborne et al., 2024), Pietropolli et al. (2024, DOI: `10.5194/gmd-17-7347-2024`), and Amadio et al. (2024, DOI: `10.5194/os-20-689-2024`). Those citations are not about sound speed specifically, but they show that local, input-dependent uncertainty for Argo-derived variables is already a mature idea elsewhere in the Argo ecosystem.

The sound-speed ML subset in the draft source list is extensive: Madiligama, Zou, and Zhang (2025, DOI: `10.1038/s44172-025-00459-6`); a 2024 STA-ConvLSTM model; a 2024 hierarchical LSTM; a 2025 *Water* random-forest paper (DOI: `10.3390/w17040539`); a 2022 South China Sea XGBoost paper (DOI: `10.3389/fmars.2022.1051820`); a 2024 LSTM paper (DOI: `10.3389/fmars.2024.1375766`); Lu et al. (2022, DOI: `10.3390/jmse10050572`); a 2021 BP-ANN *JMSE* paper; a 2025 STNet paper; and an IEEE OCEANS 2021 conference paper (DOI: `10.1109/OCEANS47282.2021.9600074`). Taken together, they suggest a field that is moving rapidly toward predictive SSP and sound-speed models, but not necessarily toward transparent uncertainty decomposition at the per-profile vertical interpolation stage.

The draft set also includes broader spatiotemporal interpolation work through Troupin et al. (2012), Barth et al. (2014, 2020, 2022), Bhaskar et al. (2021, DOI: `10.1007/s12040-021-01675-2`), Lyman and Johnson (2023), Oke et al. (2021, DOI: `10.3389/feart.2021.696985`), Jones et al. (2019, DOI: `10.1029/2018JC014629`), a 2022 *Science China Earth Sciences* GMM QC paper, a 2021 Bi-LSTM paper (DOI: `10.1155/2021/5665386`), Johnson et al. (2022, arXiv:2211.10444), Li et al. (2018), an IEEE OCEANS 2021 Indian Ocean hierarchical reconstruction paper (DOI: `10.1109/OCEANS2021.9520063`), a 2024 *Applied Ocean Research* correlation-radius study, and a 2024 *Acta Oceanologica Sinica* CORA comparison (DOI: `10.1007/s13131-024-2388-6`).

The clear implication is that an uncertainty-aware interpolation pipeline for individual profiles would not be out of step with the field. It would instead connect a missing low-level profile-processing layer to a statistical ecosystem that already expects quantified uncertainty.

## The Argo Program and Its Expanding Observational Frontier

The broader Argo context in the draft citation set is centered on Johnson et al. (2022, DOI: `10.1146/annurev-marine-022521-102008`), Riser et al. (2016, DOI: `10.1038/nclimate2872`), and Roemmich et al. (2009), plus the OneArgo planning literature through Roemmich et al. (2019), Jayne et al. (2017), and Thierry et al. (2025, DOI: `10.3389/fmars.2025.1593904`). Together these references suggest that Argo has already grown beyond a core T/S program into a multi-mission observing system with deep and biogeochemical extensions.

That matters directly for acoustics. Zilberman et al. (2023, DOI: `10.3389/fmars.2023.1287867`) and Iqbal et al. (2019) suggest that Deep Argo materially changes deep sound-speed characterization, including errors introduced by extrapolating shallower profiles downward. Cheng et al. (2026), von Schuckmann and Le Traon (2011), and Lynch et al. (~2018) suggest that climate-driven changes in heat content and stratification will continue to alter acoustic conditions over time. The draft source list also hints at downstream environmental-noise and sanctuary-monitoring links through NOAA / Navy SanctSound.

The practical takeaway is that a sound-speed-focused Argo interpolation workflow is not a niche detour. It fits naturally into a program whose scope is still broadening in exactly the directions that increase acoustic relevance.

## Conclusion: Where an Uncertainty-Aware Interpolation Pipeline Fits

Even in draft form, the current literature map points to a specific contribution gap.

The equation literature is mature. Argo-derived acoustic climatology and regional-variability studies are established. Operational and research acoustics already depend on Argo-informed sound-speed structure. Statistical and ML methods already treat uncertainty as a first-class problem in adjacent Argo applications. But the **profile-level vertical interpolation step between raw Argo T/S observations and derived sound-speed structure remains weakly documented and weakly quantified**.

That gap is exactly where this repository can contribute. A deterministic Jana et al. replication provides a legible baseline. A follow-on uncertainty-aware wrapper around linear, PCHIP, and spline-style profile interpolation can then quantify how much of the downstream variability in sound speed and acoustically relevant diagnostics is attributable not to the seawater equation or the observing platform, but to the profile-processing decision that the literature often leaves implicit.

## References

The bibliography below normalizes the current citation inventory as far as the available local metadata allows. Jana et al. (2022) has been verified against the local PDF in [sources/](sources/). All other entries remain provisional and should be checked against full text before using them as final bibliography entries or adding page-specific citations. Entries that still lack enough metadata to normalize cleanly are listed separately at the end so they remain tracked rather than disappearing from the review.

### Verified Local Source

- Jana, S., Gangopadhyay, A., Haley, P. J., Jr., & Lermusiaux, P. F. J. (2022). *Sound Speed Variability over Bay of Bengal from Argo Observations (2011-2020).* In *OCEANS 2022 - Chennai* (pp. 1-8). IEEE. https://doi.org/10.1109/OCEANSChennai45887.2022.9775509

### Provisional Bibliography

- Affatati, Scaini, and Salon (2022). Provisional entry. https://doi.org/10.1029/2021EF002099
- Akima (1970). Provisional entry. Full bibliographic metadata pending full-text review.
- Allen et al. (2017). Provisional entry. https://doi.org/10.1002/lom3.10203
- Allen et al. (2025). Provisional entry. https://doi.org/10.1002/lom3.10715
- Amadio et al. (2024). Provisional entry. https://doi.org/10.5194/os-20-689-2024
- Armansyah, Sukoco, and Pranowo (2018). Provisional entry. Full bibliographic metadata pending full-text review.
- Barker and McDougall (2020). Provisional entry. https://doi.org/10.1175/JTECH-D-19-0211.1
- Barth et al. (2014). Provisional entry. Full bibliographic metadata pending full-text review.
- Barth et al. (2020). Provisional entry. Full bibliographic metadata pending full-text review.
- Barth et al. (2022). Provisional entry. Full bibliographic metadata pending full-text review.
- Bell et al. (2009). Provisional entry. Full bibliographic metadata pending full-text review.
- Bhaskar et al. (2021). Provisional entry. https://doi.org/10.1007/s12040-021-01675-2
- Bittig et al. (2018). Provisional entry. https://doi.org/10.3389/fmars.2018.00328
- Bozzano et al. (2026). Provisional entry. https://doi.org/10.5194/os-22-101-2026
- Brewer et al. (2015). Provisional entry. https://doi.org/10.1016/j.marchem.2015.09.009
- Cabanes, Thierry, and Lagadec (2016). Provisional entry. Full bibliographic metadata pending full-text review.
- Cao et al. (2025). Provisional entry. Full bibliographic metadata pending full-text review.
- Carnes (2009). Provisional entry. Full bibliographic metadata pending full-text review.
- Carter et al. (2021). Provisional entry. https://doi.org/10.1002/lom3.10461
- Chassignet et al. (2009). Provisional entry. Full bibliographic metadata pending full-text review.
- Chassignet et al. (2020). Provisional entry. Full bibliographic metadata pending full-text review.
- Chen and Millero (1977). Provisional entry. https://doi.org/10.1121/1.381646
- Chen et al. (2017). Provisional entry. Full bibliographic metadata pending full-text review.
- Chen et al. (2018). Provisional entry. Full bibliographic metadata pending full-text review.
- Chen et al. (2020). Provisional entry. https://doi.org/10.1016/j.apacoust.2020.107478
- Cheng and Zhu (2014). Provisional entry. https://doi.org/10.1175/JTECH-D-13-00220.1
- Cheng et al. (2024). Provisional entry. https://doi.org/10.5194/essd-16-3517-2024
- Cheng et al. (2026). Provisional entry. Full bibliographic metadata pending full-text review.
- Chu and Fan (2024). Provisional entry. https://doi.org/10.1038/s41597-024-04074-6
- Chu, Haeger, et al. (2002). Provisional entry. Full bibliographic metadata pending full-text review.
- Coppens (1981). Provisional entry. Full bibliographic metadata pending full-text review.
- Cummings (2005). Provisional entry. Full bibliographic metadata pending full-text review.
- Cummings and Smedstad (2013). Provisional entry. Full bibliographic metadata pending full-text review.
- Del Grosso (1974). Provisional entry. https://doi.org/10.1121/1.1903388
- Dunn and Ridgway (2002). Provisional entry. Full bibliographic metadata pending full-text review.
- Dushaw et al. (1993). Provisional entry. https://doi.org/10.1121/1.405660
- Dushaw et al. (2009). Provisional entry. https://doi.org/10.1029/2008JC005124
- Dushaw (2019). Provisional entry. https://doi.org/10.1175/JTECH-D-18-0082.1
- Dushaw (2022). Provisional entry. https://doi.org/10.16993/tellusa.39
- Feistel (2003). Provisional entry. Full bibliographic metadata pending full-text review.
- Feistel (2008). Provisional entry. https://doi.org/10.1016/j.dsr.2008.07.004
- Feistel et al. (2010). Provisional entry. Full bibliographic metadata pending full-text review.
- Fofonoff and Millard (1983). Provisional entry. Full bibliographic metadata pending full-text review.
- Fourrier et al. (2020). Provisional entry. Full bibliographic metadata pending full-text review.
- Fritsch and Carlson (1980). Provisional entry. Full bibliographic metadata pending full-text review.
- Fujii et al. (2024). Provisional entry. https://doi.org/10.3389/fmars.2024.1496409
- Gaillard et al. (2016). Provisional entry. https://doi.org/10.1175/JCLI-D-15-0028.1
- Good, Martin, and Rayner (2013). Provisional entry. https://doi.org/10.1002/2013JC009067
- Gouretski (2018). Provisional entry. https://doi.org/10.5194/os-14-1127-2018
- Grekov, Grekov, and Sychov (2021). Provisional entry. https://doi.org/10.1016/j.measurement.2021.109073
- He et al. (2024). Provisional entry. Full bibliographic metadata pending full-text review.
- Hjelmervik, Jensen, and Ostenstad (2012). Provisional entry. https://doi.org/10.1007/s10236-011-0499-z
- Hjelmervik and Hjelmervik (2013). Provisional entry. https://doi.org/10.1007/s10236-013-0623-3
- IOC, SCOR, and IAPSO (2010). Provisional entry. Full bibliographic metadata pending full-text review.
- Iqbal et al. (2019). Provisional entry. Full bibliographic metadata pending full-text review.
- Jayne et al. (2017). Provisional entry. Full bibliographic metadata pending full-text review.
- Jean-Michel et al. (2021). Provisional entry. Full bibliographic metadata pending full-text review.
- Johnson et al. (2022a). Provisional entry. https://doi.org/10.1146/annurev-marine-022521-102008
- Johnson et al. (2022b). Provisional entry. https://arxiv.org/abs/2211.10444
- Jones et al. (2019). Provisional entry. https://doi.org/10.1029/2018JC014629
- Katsura (2021). Provisional entry. https://doi.org/10.1029/2020JC016591
- Kobayashi et al. (2019). Provisional entry. https://doi.org/10.1186/s40645-019-0310-1
- Korean Acoustical Society (2021). Provisional entry. Full bibliographic metadata pending full-text review.
- Kuusela and Stein (2018). Provisional entry. https://doi.org/10.1098/rspa.2018.0400
- Le Traon et al. (2019). Provisional entry. Full bibliographic metadata pending full-text review.
- Lellouche et al. (2018). Provisional entry. Full bibliographic metadata pending full-text review.
- Leroy, Robinson, and Goldsmith (2008). Provisional entry. https://doi.org/10.1121/1.2988296
- Li et al. (2017). Provisional entry. https://doi.org/10.1002/2016JC012285
- Li et al. (2018). Provisional entry. Full bibliographic metadata pending full-text review.
- Li et al. (2022). Provisional entry. https://doi.org/10.1029/2022GL101079
- Liu et al. (2024). Provisional entry. https://doi.org/10.1029/2023JC020871
- Lu et al. (2022). Provisional entry. https://doi.org/10.3390/jmse10050572
- Lyman and Johnson (2023). Provisional entry. Full bibliographic metadata pending full-text review.
- Mackenzie (1981). Provisional entry. https://doi.org/10.1121/1.386920
- Madiligama, Zou, and Zhang (2025). Provisional entry. https://doi.org/10.1038/s44172-025-00459-6
- Mandelberg and Frizzell-Makowski (2000). Provisional entry. Full bibliographic metadata pending full-text review.
- McDougall et al. (2003). Provisional entry. Full bibliographic metadata pending full-text review.
- Meinen and Watts (1997). Provisional entry. https://doi.org/10.1121/1.419655
- Millero and Li (1994). Provisional entry. https://doi.org/10.1121/1.409844
- Munk, Worcester, and Wunsch (1995). Provisional entry. Full bibliographic metadata pending full-text review.
- North and Livingstone (2013). Provisional entry. Full bibliographic metadata pending full-text review.
- Oke et al. (2021). Provisional entry. https://doi.org/10.3389/feart.2021.696985
- Osborne et al. (2024). Provisional entry. Full bibliographic metadata pending full-text review.
- Owens and Wong (2009). Provisional entry. Full bibliographic metadata pending full-text review.
- Park, Kuusela, Giglio, and Gray (2023). Provisional entry. https://doi.org/10.1214/22-AOAS1679
- Pawlowicz et al. (2012). Provisional entry. Full bibliographic metadata pending full-text review.
- Penupothu (2025). Provisional entry. https://doi.org/10.21227/61qc-z803
- Pietropolli et al. (2024). Provisional entry. https://doi.org/10.5194/gmd-17-7347-2024
- Pike and Beiboer (1993). Provisional entry. Full bibliographic metadata pending full-text review.
- Possenti et al. (2023). Provisional entry. https://doi.org/10.7717/peerj.16208
- Reiniger and Ross (1968). Provisional entry. https://doi.org/10.1016/0011-7471(68)90040-5
- Ridgway, Dunn, and Wilkin (2002). Provisional entry. Full bibliographic metadata pending full-text review.
- Riser et al. (2016). Provisional entry. https://doi.org/10.1038/nclimate2872
- Roemmich and Gilson (2009). Provisional entry. https://doi.org/10.1016/j.pocean.2009.03.004
- Roemmich et al. (2009). Provisional entry. Full bibliographic metadata pending full-text review.
- Roemmich et al. (2019). Provisional entry. Full bibliographic metadata pending full-text review.
- Roquet et al. (2015). Provisional entry. https://doi.org/10.1016/j.ocemod.2015.04.002
- Salon et al. (2003). Provisional entry. Full bibliographic metadata pending full-text review.
- Sauzede et al. (2017). Provisional entry. https://doi.org/10.3389/fmars.2017.00128
- Schmidtko, Johnson, and Lyman (2013). Provisional entry. https://doi.org/10.1002/jgrc.20122
- Spiesberger (1993). Provisional entry. Full bibliographic metadata pending full-text review.
- Spiesberger and Metzger (1991a). Provisional entry. Full bibliographic metadata pending full-text review.
- Spiesberger and Metzger (1991b). Provisional entry. Full bibliographic metadata pending full-text review.
- Srinivasu et al. (2024). Provisional entry. https://doi.org/10.1029/2023EA003497
- Su et al. (2023). Provisional entry. https://doi.org/10.3389/fmars.2023.1121334
- Swaminathan and Bhaskaran (2009). Provisional entry. Full bibliographic metadata pending full-text review.
- Teague, Carron, and Hogan (1990). Provisional entry. Full bibliographic metadata pending full-text review.
- Thierry et al. (2025). Provisional entry. https://doi.org/10.3389/fmars.2025.1593904
- Tonani et al. (2015). Provisional entry. Full bibliographic metadata pending full-text review.
- Troupin et al. (2012). Provisional entry. Full bibliographic metadata pending full-text review.
- Udaya Bhaskar, Swain, and Ravichandran (2008). Provisional entry. https://doi.org/10.1007/BF03020695
- Udaya Bhaskar et al. (2012). Provisional entry. Full bibliographic metadata pending full-text review.
- Udaya Bhaskar and Swain (2016). Provisional entry. Full bibliographic metadata pending full-text review.
- von Schuckmann and Le Traon (2011). Provisional entry. Full bibliographic metadata pending full-text review.
- Wilson (1960). Provisional entry. Full bibliographic metadata pending full-text review.
- Wong and Zhu (1995). Provisional entry. https://doi.org/10.1121/1.413048
- Wong et al. (2020). Provisional entry. https://doi.org/10.3389/fmars.2020.00700
- Wong, Gilson, and Cabanes (2023). Provisional entry. https://doi.org/10.5194/essd-15-383-2023
- Wong, Johnson, and Owens (2003). Provisional entry. Full bibliographic metadata pending full-text review.
- Woolfe et al. (2015). Provisional entry. https://doi.org/10.1002/2015GL063438
- Xu et al. (2009). Provisional entry. Full bibliographic metadata pending full-text review.
- Yu et al. (2022). Provisional entry. https://doi.org/10.3389/fmars.2022.1030980
- Zhang et al. (2023). Provisional entry. https://doi.org/10.1007/s10872-023-00701-9
- Zhou et al. (2023). Provisional entry. https://doi.org/10.1029/2022JC019386
- Zilberman et al. (2023). Provisional entry. https://doi.org/10.3389/fmars.2023.1287867

### Cited Works Pending Full Bibliographic Recovery

- 2021 *JMSE* BP-ANN paper cited in the machine-learning section. Full author, title, and DOI metadata pending.
- 2021 IEEE OCEANS conference paper cited in the machine-learning section. https://doi.org/10.1109/OCEANS47282.2021.9600074
- 2021 Bi-LSTM paper cited in the interpolation and machine-learning section. https://doi.org/10.1155/2021/5665386
- 2022 GDCSM-Argo product cited in the interpolation section. Full author, title, and DOI metadata pending.
- 2022 *Science China Earth Sciences* GMM QC paper cited in the machine-learning section. Full author, title, and DOI metadata pending.
- 2022 South China Sea XGBoost sound-speed paper cited in the machine-learning section. https://doi.org/10.3389/fmars.2022.1051820
- 2023 *Frontiers in Marine Science* sound-channel classification paper cited in the regional-variability section. https://doi.org/10.3389/fmars.2023.1130061
- 2024 *Acta Oceanologica Sinica* CORA comparison paper cited in the machine-learning section. https://doi.org/10.1007/s13131-024-2388-6
- 2024 *Applied Ocean Research* correlation-radius study cited in the machine-learning section. Full author, title, and DOI metadata pending.
- 2024 *Frontiers in Marine Science* convergence-zone prediction paper cited in the acoustic-applications section. https://doi.org/10.3389/fmars.2024.1364884
- 2024 *Frontiers in Marine Science* LSTM sound-speed paper cited in the machine-learning section. https://doi.org/10.3389/fmars.2024.1375766
- 2024 *Remote Sensing* South China Sea eddy-effects paper cited in the regional-variability section. Full author, title, and DOI metadata pending.
- 2024 STA-ConvLSTM sound-speed paper cited in the machine-learning section. Full author, title, and DOI metadata pending.
- 2024 hierarchical LSTM sound-speed paper cited in the machine-learning section. Full author, title, and DOI metadata pending.
- 2025 *Frontiers in Marine Science* eddy-parameterized propagation-loss paper cited in the acoustic-applications section. https://doi.org/10.3389/fmars.2025.1588066
- 2025 *JMSE* convergence-zone paper cited in the acoustic-applications section. Full author, title, and DOI metadata pending.
- 2025 STNet sound-speed paper cited in the machine-learning section. Full author, title, and DOI metadata pending.
- 2025 *Water* random-forest paper cited in the machine-learning section. https://doi.org/10.3390/w17040539
- IEEE OCEANS 2021 Indian Ocean hierarchical reconstruction paper cited in the machine-learning section. https://doi.org/10.1109/OCEANS2021.9520063
- Lynch et al. (~2018) climate and acoustics reference cited in the Argo-program section. Exact year and bibliographic metadata pending.
- NATO CMRE Arctic acoustics work cited in the acoustic-applications section. Exact year and bibliographic metadata pending.
- NOAA / Navy SanctSound references cited in the Argo-program section. Exact document selection and bibliographic metadata pending.
- Nystuen et al. (~2014) passive-acoustics bridge reference cited in the acoustic-applications section. Exact year and bibliographic metadata pending.
- Prasanna Kumar and Somayajulu (year pending) Indian Ocean sound-channel reference cited in the regional-variability section. Full bibliographic metadata pending.
