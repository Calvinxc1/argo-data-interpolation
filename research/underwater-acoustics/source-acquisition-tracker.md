# Underwater Acoustics Source Acquisition Tracker

This note tracks which bibliography entries in [literature-review.md](literature-review.md) still need local full-text material. Linked references with local copies already wired into the literature review are not repeated here.

## Summary

- Last updated: 2026-04-14
- References in bibliography: `150`
- References with linked local PDF copies: `129`
- References resolved via canonical non-article web pages: `4`
- References still missing local PDF full-text material: `18`
- Missing full-text media-type breakdown: `13` journal articles, `3` conference or presentation publications, `1` book, `1` special publication/report.
- Local `.pdf` files remain the required resolved format for article and book sources; non-article web-native resources may resolve through a stable canonical landing page.

## Status Legend

- `timed_out`: official full-text host found, but fetch attempt timed out
- `blocked_pdf_endpoint`: official article identified, but publisher or repository blocked CLI fetches
- `subscription_preview_only`: official article page is reachable, but only abstract or preview content is exposed without subscription access
- `metadata_only`: citation metadata was verified, but no stable official online full-text host was identified in this pass
- `html_capture_only`: publisher or journal HTML appears to expose article full text, but no local PDF is available and local HTML captures are not stored in this repo, so the citation remains unresolved for local full-text verification
- `web_native_complete`: the cited resource is a web-native non-article item and is resolved through its canonical landing page
- `wrong_artifact`: a fetched file did not match the cited article and should not be linked
- `host_issue`: the official host had certificate, routing, or URL problems during fetch attempts
- `ill_requested`: an interlibrary loan request has been submitted for the cited item; notes should preserve the current acquisition blocker or source-host detail

## Unresolved References

### Journal Articles

#### The Journal of the Acoustical Society of America

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | Coppens, A. B. “Simple Equations for the Speed of Sound in Neptunian Waters.” The Journal of the Acoustical Society of America, vol. 69, no. 3, Mar. 1981, pp. 862–63. https://doi.org/10.1121/1.385486. | `ill_requested` | AIP / JASA | 2026-04-06 | DOI resolves to the AIP Publishing / JASA article host, but CLI fetches terminate in a Cloudflare challenge page instead of article content. |
| 2 | Del Grosso, V. A. “New Equation for the Speed of Sound in Natural Waters (with Comparisons to Other Equations).” The Journal of the Acoustical Society of America, vol. 56, no. 4, Oct. 1974, pp. 1084–91. https://doi.org/10.1121/1.1903388. | `ill_requested` | AIP / JASA | 2026-04-06 | DOI resolves to the AIP Publishing / JASA article host, but CLI fetches terminate in a Cloudflare challenge page instead of article content. |
| 3 | Mackenzie, Kenneth V. “Nine-Term Equation for Sound Speed in the Oceans.” The Journal of the Acoustical Society of America, vol. 70, no. 3, Sept. 1981, pp. 807–12. https://doi.org/10.1121/1.386920. | `ill_requested` | AIP / JASA | 2026-04-06 | DOI resolves to the AIP Publishing / JASA article host, but CLI fetches terminate in a Cloudflare challenge page instead of article content. |
| 4 | Spiesberger, John L. “Is Del Grosso’s Sound-Speed Algorithm Correct?” The Journal of the Acoustical Society of America, vol. 93, no. 4, Apr. 1993, pp. 2235–37. https://doi.org/10.1121/1.406686. | `ill_requested` | AIP / JASA | 2026-04-06 | DOI resolves to the AIP Publishing / JASA article host, but CLI fetches terminate in a Cloudflare challenge page instead of article content. |
| 5 | Spiesberger, John L., and Kurt Metzger. “A New Algorithm for Sound Speed in Seawater.” The Journal of the Acoustical Society of America, vol. 89, no. 6, June 1991, pp. 2677–88. https://doi.org/10.1121/1.400707. | `ill_requested` | AIP / JASA | 2026-04-06 | DOI resolves to the AIP Publishing / JASA article host, but CLI fetches terminate in a Cloudflare challenge page instead of article content. |
| 6 | Wilson, Wayne D. “Speed of Sound in Sea Water as a Function of Temperature, Pressure, and Salinity.” The Journal of the Acoustical Society of America, vol. 32, no. 6, June 1960, pp. 641–44. https://doi.org/10.1121/1.1908167. | `ill_requested` | AIP / JASA | 2026-04-06 | DOI resolves to the AIP Publishing / JASA article host, but CLI fetches terminate in a Cloudflare challenge page instead of article content. |
| 7 | Wong, George S. K., and Shi-ming Zhu. “Speed of Sound in Seawater as a Function of Salinity, Temperature, and Pressure.” The Journal of the Acoustical Society of America, vol. 97, no. 3, Mar. 1995, pp. 1732–36. https://doi.org/10.1121/1.413048. | `ill_requested` | AIP / JASA | 2026-04-06 | DOI resolves to the AIP Publishing / JASA article host, but CLI fetches terminate in a Cloudflare challenge page instead of article content. |

#### Elsevier Journals

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 8 | Chen, Cheng, et al. “Investigating Acoustic Propagation in the Sonic Duct Related with Subtropical Mode Water in Northwestern Pacific Ocean.” Applied Acoustics, vol. 169, Dec. 2020, p. 107478. https://doi.org/10.1016/j.apacoust.2020.107478. | `ill_requested` | Elsevier / ScienceDirect | 2026-04-06 | DOI resolves through Elsevier linking hub to the ScienceDirect article URL, but direct CLI fetches return a generic challenge page rather than article content. |
| 9 | Grekov, Aleksandr N., et al. “Estimating Quality of Indirect Measurements of Sea Water Sound Velocity by CTD Data.” Measurement, vol. 175, Apr. 2021, p. 109073. https://doi.org/10.1016/j.measurement.2021.109073. | `ill_requested` | Elsevier / ScienceDirect | 2026-04-06 | DOI resolves through Elsevier linking hub to the ScienceDirect article URL, but direct CLI fetches return a generic challenge page rather than article content. |
#### AGU / Wiley

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 10 | Spiesberger, John L., and Kurt Metzger. “Basin-Scale Tomography: A New Tool for Studying Weather and Climate.” Journal of Geophysical Research: Oceans, vol. 96, no. C3, Mar. 1991, pp. 4869–89. https://doi.org/10.1029/90JC02538. | `ill_requested` | AGU / Wiley | 2026-04-06 | DOI resolves to the AGU/Wiley article host, but CLI fetches terminate in a Cloudflare challenge page instead of article content. |

#### Journal of Ship Technology

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 11 | Swaminathan, V. S., and B. Prasad Kumar. “Variability in Sound Speed Structure and SOFAR Channel Depth in the Indian Ocean.” Journal of Ship Technology, vol. 5, 2009, pp. 53–72. | `ill_requested` | unknown | 2026-04-06 | No DOI or stable official online host is present in the citation metadata used here; manual acquisition is required. |

#### Acta Oceanologica Sinica

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 12 | Tao, Shiyuan, et al. “Analysis of the Distribution of Sound Velocity Profiles and Sound Propagation Laws Based on a Global High-Resolution Ocean Reanalysis Product.” Acta Oceanologica Sinica, vol. 44, no. 5, May 2025, pp. 131–49. https://doi.org/10.1007/s13131-024-2388-6. | `ill_requested` | Acta Oceanologica Sinica | 2026-04-07 | Article full text appears to be available via the journal HTML page, but no local PDF is stored and this repo does not keep local HTML captures, so the citation remains unresolved for local full-text verification. |

#### Journal of Oceanography

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 13 | Zhang, Gengming, et al. “Subsurface Sound Channel and Seasonal Variation of Its Characteristics in the Mid-Latitude of Northwest Pacific.” Journal of Oceanography, vol. 79, no. 6, Aug. 2023, pp. 619–27. https://doi.org/10.1007/s10872-023-00701-9. | `ill_requested` | Journal of Oceanography | 2026-04-07 | Article full text appears to be available via the journal HTML page, but no local PDF is stored and this repo does not keep local HTML captures, so the citation remains unresolved for local full-text verification. |
### Conference and Presentation Publications

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 14 | Iqbal, Khan, A. G. Bhaskara Rao, Y. Ashok Kumar, and T. V. S. Udaya Bhaskar. “Significance of Deep Argo Data in Computation of Sound Speed in Deep Oceanic Waters.” Underwater Acoustics Conference & Exhibition, 2019. | `metadata_only` | unknown | 2026-04-10 | A related later journal article is now stored locally as `sources/iqbal-2020-symmetrical_and_asymmetrical_rectifications_for_deeper_ocean_ctd_ssp_extrapolations.pdf`, but it is not the cited 2019 conference publication, so this conference citation still remains unresolved. |
| 15 | Mandelberg, M. D., and L. J. Frizzell-Makowski. “Acoustic Provincing of Ocean Basins.” OCEANS 2000 MTS/IEEE Conference and Exhibition, 2000, pp. 105–08. | `metadata_only` | unknown | 2026-04-06 | No DOI or stable official online host is present in the citation metadata used here; manual acquisition is required. |
| 16 | Nystuen, Jeffrey A., Stephen C. Riser, T. Wen, and D. Swift. “Interpreted Acoustic Ocean Observations from Argo Floats.” The Journal of the Acoustical Society of America, vol. 129, no. 4, Apr. 2011, p. 2400. https://doi.org/10.1121/1.3587814. | `blocked_pdf_endpoint` | AIP / JASA | 2026-04-06 | DOI resolves to the AIP Publishing / JASA article host, but CLI fetches terminate in a Cloudflare challenge page instead of article content. SFCC library appears to indicate a full-text copy is available, but the linked pages do not presently support actually retrieving it. This appears to be a meeting or presentation-style publication rather than a standard journal article. |

### Book

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 17 | Munk, Walter, Peter Worcester, and Carl Wunsch. Ocean Acoustic Tomography. Cambridge University Press, 1995. Cambridge Monographs on Mechanics. https://doi.org/10.1017/CBO9780511666926. | `ill_requested` | Cambridge | 2026-04-06 | DOI resolves to the Cambridge Core book landing page, but the full book text is not exposed in this environment. |

### Special Publication / Report

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 18 | Pike, J. M., and F. L. Beiboer. A Comparison between Algorithms for the Speed of Sound in Seawater. The Hydrographic Society, 1993. Special Publication 34. | `metadata_only` | unknown | 2026-04-06 | No DOI or stable official online host is present in the citation metadata used here; manual acquisition is required. |
