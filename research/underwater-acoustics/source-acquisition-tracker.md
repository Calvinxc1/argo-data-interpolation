# Underwater Acoustics Source Acquisition Tracker

This note tracks which active bibliography entries in [literature-review.md](literature-review.md) still need local full-text material. Linked references with local copies already wired into the literature review are not repeated here. It also retains archived acquisition records for removed citations when that acquisition history is still useful to keep.

## Summary

- Last updated: 2026-04-15
- References in active bibliography: `150`
- References with linked local PDF copies: `137`
- References resolved via canonical non-article web pages: `5`
- References still missing local PDF full-text material: `8`
- Missing full-text media-type breakdown: `3` journal articles, `3` conference or presentation publications, `1` book, `1` special publication/report.
- Archived acquisition records excluded from active tallies: `1`
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
- `unobtainable`: acquisition attempts have been exhausted or have failed, so the record is kept only as an archived history item rather than an active pending source

## Unresolved References

### Journal Articles

#### The Journal of the Acoustical Society of America

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | Mackenzie, Kenneth V. “Nine-Term Equation for Sound Speed in the Oceans.” The Journal of the Acoustical Society of America, vol. 70, no. 3, Sept. 1981, pp. 807–12. https://doi.org/10.1121/1.386920. | `ill_requested` | AIP / JASA | 2026-04-06 | DOI resolves to the AIP Publishing / JASA article host, but CLI fetches terminate in a Cloudflare challenge page instead of article content. |
| 2 | Spiesberger, John L., and Kurt Metzger. “A New Algorithm for Sound Speed in Seawater.” The Journal of the Acoustical Society of America, vol. 89, no. 6, June 1991, pp. 2677–88. https://doi.org/10.1121/1.400707. | `ill_requested` | AIP / JASA | 2026-04-06 | DOI resolves to the AIP Publishing / JASA article host, but CLI fetches terminate in a Cloudflare challenge page instead of article content. |

#### Elsevier Journals

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 3 | Grekov, Aleksandr N., et al. “Estimating Quality of Indirect Measurements of Sea Water Sound Velocity by CTD Data.” Measurement, vol. 175, Apr. 2021, p. 109073. https://doi.org/10.1016/j.measurement.2021.109073. | `ill_requested` | Elsevier / ScienceDirect | 2026-04-06 | DOI resolves through Elsevier linking hub to the ScienceDirect article URL, but direct CLI fetches return a generic challenge page rather than article content. |
### Conference and Presentation Publications

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 4 | Iqbal, Khan, A. G. Bhaskara Rao, Y. Ashok Kumar, and T. V. S. Udaya Bhaskar. “Significance of Deep Argo Data in Computation of Sound Speed in Deep Oceanic Waters.” Underwater Acoustics Conference & Exhibition, 2019. | `metadata_only` | unknown | 2026-04-10 | A related later journal article is now stored locally as `sources/iqbal-2020-symmetrical_and_asymmetrical_rectifications_for_deeper_ocean_ctd_ssp_extrapolations.pdf`, but it is not the cited 2019 conference publication, so this conference citation still remains unresolved. |
| 5 | Mandelberg, M. D., and L. J. Frizzell-Makowski. “Acoustic Provincing of Ocean Basins.” OCEANS 2000 MTS/IEEE Conference and Exhibition, 2000, pp. 105–08. | `subscription_preview_only` | IEEE Xplore | 2026-04-15 | Official IEEE Xplore landing page identified at `https://ieeexplore.ieee.org/document/881241`, but no local PDF is stored and full text appears to remain access-controlled from the article host. |
| 6 | Nystuen, Jeffrey A., Stephen C. Riser, T. Wen, and D. Swift. “Interpreted Acoustic Ocean Observations from Argo Floats.” The Journal of the Acoustical Society of America, vol. 129, no. 4, Apr. 2011, p. 2400. https://doi.org/10.1121/1.3587814. | `blocked_pdf_endpoint` | AIP / JASA | 2026-04-06 | DOI resolves to the AIP Publishing / JASA article host, but CLI fetches terminate in a Cloudflare challenge page instead of article content. SFCC library appears to indicate a full-text copy is available, but the linked pages do not presently support actually retrieving it. This appears to be a meeting or presentation-style publication rather than a standard journal article. |

### Book

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 7 | Munk, Walter, Peter Worcester, and Carl Wunsch. Ocean Acoustic Tomography. Cambridge University Press, 1995. Cambridge Monographs on Mechanics. https://doi.org/10.1017/CBO9780511666926. | `ill_requested` | Cambridge | 2026-04-06 | DOI resolves to the Cambridge Core book landing page, but the full book text is not exposed in this environment. |

### Special Publication / Report

| # | Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- | --- |
| 8 | Pike, J. M., and F. L. Beiboer. A Comparison between Algorithms for the Speed of Sound in Seawater. The Hydrographic Society, 1993. Special Publication 34. | `metadata_only` | unknown | 2026-04-06 | No DOI or stable official online host is present in the citation metadata used here; manual acquisition is required. |

## Archived Acquisition Records

These records are kept for acquisition-history purposes only and are excluded from the active bibliography tallies above.

| Citation | Status | Source host | Last attempt | Notes |
| --- | --- | --- | --- | --- |
| Swaminathan, V. S., and B. Prasad Kumar. “Variability in Sound Speed Structure and SOFAR Channel Depth in the Indian Ocean.” Journal of Ship Technology, vol. 5, 2009, pp. 53–72. | `unobtainable` | unknown | 2026-04-06 | No DOI or stable official online host is present in the citation metadata used here; acquisition attempts did not produce the full text. Removed from the active literature-review bibliography on 2026-04-15 after concluding that the current review did not materially depend on it. |
