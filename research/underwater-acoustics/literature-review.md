# Underwater Acoustics: A Literature Review

This review covers the source-backed material currently verified for the `underwater-acoustics` topic. The present version is intentionally narrow. It anchors the topic on a public Argo-to-sound-speed study that can serve as a downstream demonstration target for uncertainty-aware interpolation and uncertainty propagation work.

Broader coverage of acoustic propagation tools, uncertainty-propagation methods, and operational sonar or survey workflows is pending source acquisition and verification for this topic.

---

## Anchor Study: Jana et al. (2022)

Jana et al. (2022) analyzed sound-speed variability in the Bay of Bengal using Argo observations from 2011 through 2020. The paper frames sound-speed structure as operationally relevant because it affects underwater refraction, sonic layer depth, surface ducting, and shadow-zone formation. The study therefore sits directly on the bridge between Argo hydrography and downstream acoustic interpretation.

The paper's workflow is straightforward and reproducible. Temperature and salinity profiles were obtained from the Coriolis Argo archive for the Indian Ocean. The authors report that they applied standard Argo automated quality checks plus additional statistical and visual screening, removed profiles with values outside two standard deviations of the mean profiles, and retained only profiles that included at least one observation within the upper 20 m and extended to 500 m or deeper. After filtering, 14,246 profiles remained in the analysis. Sound speed was then estimated from the Argo temperature and salinity profiles using the UNESCO equation, and the temperature, salinity, and sound-speed profiles were interpolated onto a regular 1 m vertical grid from 5 m to 500 m.

The downstream analysis is also well aligned with the present project's intended audience. Jana et al. examined monthly and depth-dependent variability in sound speed, identified the largest sound-speed standard deviation near 110 m in the thermocline region, and discussed the implications of positive near-surface sound-speed gradients for sonic layer depth, surface ducting, and shadow zones in the northern Bay of Bengal. This makes the paper a useful anchor because it stays close to acoustically legible outcomes rather than stopping at hydrographic reconstruction alone.

## Why This Study Is a Strong Replication Target

Jana et al. (2022) is a strong downstream benchmark for this project for three source-backed reasons.

First, the input data are public Argo profiles and the profile-processing pipeline is described at a level that is reproducible without proprietary infrastructure. Second, the study explicitly converts Argo temperature and salinity profiles into derived sound-speed profiles on a uniform depth grid, which is exactly the transition point where an uncertainty-aware interpolation wrapper would intervene. Third, the outputs are acoustically meaningful quantities such as sound-speed variability structure and sonic-layer-related interpretation, making the study more legible to an underwater-acoustics audience than a purely statistical interpolation benchmark.

The current verified source base does not show Jana et al. attaching per-profile interpolation uncertainty, propagating Argo measurement-error fields through the vertical gridding step, or carrying uncertainty through to downstream acoustic model outputs. That omission is not a criticism of the paper's goals; it is what makes the study useful here as a deterministic baseline for a replication-and-extension exercise.

## Review Boundary

The verified source coverage for this topic currently includes the Jana et al. paper only. Candidate next additions include primary-source documentation for acoustic propagation tools, public descriptions of Python wrappers used to drive those tools, and source-backed studies on sonar, navigation, survey, or acoustic-communications sensitivity to sound-speed uncertainty. Until those sources are reviewed and added here, related claims belong in working notes as pending verification rather than canonical support.

---

## References

- Jana, S., Gangopadhyay, A., Haley, P. J., Jr., & Lermusiaux, P. F. J. (2022, February). Sound speed variability over Bay of Bengal from Argo observations (2011-2020). In *OCEANS 2022 - Chennai* (pp. 1-8). IEEE. https://doi.org/10.1109/OCEANSChennai45887.2022.9775509
