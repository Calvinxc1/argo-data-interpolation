# Literature Review Project Framing Notes

This note preserves project-facing implications that were removed from the canonical literature review to keep that file focused on source-backed synthesis.

## Project Implications Extracted From the Literature Review

The sound-speed-equation literature gives this project a clean baseline-versus-upgrade framing. A deterministic baseline can use the legacy equation path from the replicated workflow, while a separate upgrade path can introduce TEOS-10 / GSW so equation-of-state effects are not conflated with interpolation effects. Lit-review anchor: [Sound Speed Equations: From UNESCO to TEOS-10](../literature-review.md#sound-speed-equations-from-unesco-to-teos-10).

The Argo-derived regional acoustics literature shows that Jana et al. is not an isolated case. That makes Jana et al. a defensible replication target because it sits inside a broader Argo-enabled acoustics literature where regional structure, sound-channel metrics, and downstream propagation relevance are already established. Lit-review anchor: [Argo-Derived Sound Speed Climatologies and Regional Variability](../literature-review.md#argo-derived-sound-speed-climatologies-and-regional-variability).

The clearest literature-backed opening for the current project is a per-profile interpolation study for derived sound speed. Adjacent ocean heat-content work shows that interpolation can materially affect derived ocean quantities, while the draft acoustics source set does not yet show an explicit per-profile interpolation comparison for derived sound-speed structure. Lit-review anchor: [Vertical Interpolation Methods Remain Under-Reported](../literature-review.md#vertical-interpolation-methods-remain-under-reported).

The literature already provides ingredients for a sensor-to-sound-speed uncertainty chain, but the interpolation step still appears weakly integrated into that chain for individual Argo profiles. That makes interpolation uncertainty the most focused methodological addition. Lit-review anchor: [Uncertainty Quantification: Sensor Precision Versus Mapping Error](../literature-review.md#uncertainty-quantification-sensor-precision-versus-mapping-error).

The draft working estimate for Argo sensor-level sound-speed uncertainty is on the order of 0.04 m/s, with temperature dominating, salinity secondary, and pressure contributing more strongly at depth. This remains a project-note assumption until it is re-derived or checked against full-text error-propagation sources, especially Grekov et al. (2021).

The operational-acoustics literature makes a deterministic Argo-to-sound-speed replication legible. The project does not need to prove that sound speed matters for acoustics; the useful contribution is to quantify how interpolation and uncertainty matter once sound speed is already in the acoustic workflow. Lit-review anchor: [Acoustic Applications Increasingly Depend on Argo](../literature-review.md#acoustic-applications-increasingly-depend-on-argo).

The gridded-product and tooling gap is now sharper than the earlier draft implied. Roemmich-Gilson remains a dominant Argo climatology, but Kuusela and Stein explicitly call out its lack of uncertainty estimates, and the public `argopy` tooling layer is positioned around access and manipulation rather than uncertainty quantification. That creates a clean opening for a library contribution framed as operationalizing uncertainty, not merely exposing more Argo data.

The operational dependency is also more concrete. HYCOM/NCODA operationally assimilates Argo temperature and salinity profiles, and official Navy-facing SBIR language states that deployed systems consume NCOM/HYCOM sound-speed and current fields for transmission-loss and target-localization workflows. The project therefore reads more cleanly as source-level risk quantification for downstream acoustics than as interpolation methodology for its own sake.

For the current Underwater Intervention abstract path, the safest claim boundary is deliberately narrow: a Jana et al. replication with uncertainty attached through Jason's library. The MRST-PCHIP Python path should be treated as optional upside rather than as abstract-critical scope.

The machine-learning and statistical Argo literature suggests that an uncertainty-aware interpolation pipeline for individual profiles would be aligned with broader field practice. The project can connect a missing low-level profile-processing layer to a statistical ecosystem that already expects quantified uncertainty. Lit-review anchor: [Machine Learning and Statistical Methods Advance Rapidly](../literature-review.md#machine-learning-and-statistical-methods-advance-rapidly).

The expanding Argo program makes a sound-speed-focused interpolation workflow relevant beyond a narrow regional case. Deep, biogeochemical, and passive-acoustic extensions all increase the value of reliable profile-level processing. Lit-review anchor: [The Argo Program and Its Expanding Observational Frontier](../literature-review.md#the-argo-program-and-its-expanding-observational-frontier).

## Candidate Contribution Framing

A deterministic Jana et al. replication provides a legible baseline. A follow-on uncertainty-aware wrapper around linear, PCHIP, and spline-style profile interpolation can then quantify how much downstream variability in sound speed and acoustically relevant diagnostics is attributable not to the seawater equation or the observing platform, but to the profile-processing decision that the literature often leaves implicit.
