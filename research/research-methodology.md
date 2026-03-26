# Research Methodology

This document describes the source-review and verification approach used in the project's research documents, including literature reviews, topic notes, and source-backed notebook commentary.

## Overview

The review process was conducted in stages rather than as a single-pass reading exercise. Initial source discovery and draft synthesis were carried out with AI assistance, then followed by a second pass focused on citation checking, comparison across related project materials, and alignment with the implemented methods under study. Final claims were then checked manually against the strongest available source material before being retained in the research documents.

For this project, the first discovery pass used Anthropic Claude Research to identify relevant sources, gather citation-linked summaries, and explore adjacent lines of evidence through iterative search. A second refinement pass used OpenAI Codex to help reconcile claims across the literature review, working notes, notebook commentary, and the implemented methods in the code, making it easier to identify citation mismatches, scope differences, and places where document wording had drifted away from the underlying sources or implementation.

Claims included in the final research documents were then checked manually against available full-text articles and supporting source documents where possible. In formal literature reviews and other source-backed commentary, page numbers were added to in-text citations only after direct verification from those full-text sources.

## Topic Source of Truth

Within each topic folder, `literature-review.md` is the canonical source-backed document for that topic. Topic notes and notebooks may interpret, synthesize, hypothesize, and plan, but any source-backed claim they make should trace to a source already covered in that topic literature review.

In practice, that means notes and notebooks should not become parallel literature reviews. If a note or notebook requires a new source-backed claim not yet covered in the literature review, the literature review should be updated first or in the same change. Candidate future sources may still be mentioned in notes as acquisition targets or pending-review items, but they should not be presented there as established support until the topic literature review has been updated accordingly.

## Verification Approach

Source-backed claims were included only when they could be supported by the cited material. When full-text access was available, those claims were checked directly against the original source. Page-specific citations were added after direct verification from the full text.

For topic notes and notebooks, this verification requirement is not weaker than it is for literature reviews. The difference is document purpose, not citation discipline. Notes may contain inference, hypothesis, implementation assumptions, and research-planning commentary, but when they make source-backed claims those claims should use the same verified source base represented in the topic literature review.

Not all sources were equally available at the same time. When full-text access was delayed or unavailable, citation metadata could still be retained in provisional form, but interpretive claims tied to those references were treated as subject to revision after full-text review.

## Role of AI Assistance

AI assistance supported source discovery, draft synthesis, citation cleanup, and consistency review across related research materials. It was used as an aid to finding, organizing, and comparing sources, not as the final authority on source content.

Final responsibility for retained claims, citation metadata, and page-specific attributions remained with manual review against the original sources. At the same time, this methodology recognizes that human review reduces but does not eliminate the possibility of error.

## Provisional References

Some references may remain provisional when full-text access is delayed or unavailable. In those cases, the research documents identify the affected sources in a short status note, retain the best-verified citation metadata available at the time of writing, and treat interpretive claims tied to those references as open to revision after full-text review.
