# Method Comparison Notes: Argo Cycle Representation

These notes compare the main method families now present in the `argo-cycle-representation` topic: exact interpolants, the historical custom curvature-adaptive spline prototype, and the simpler native spline-family alternatives that became central in notebook 03. This file is a working interpretation note, not a standalone source-backed review. Source-backed method descriptions belong in [../literature-review.md](../literature-review.md).

## How to read the comparisons

The project now has a staged method story:

1. notebook 01 established that the custom curvature-adaptive least-squares spline was a real, working compact-representation prototype,
2. notebook 02 showed that this prototype gives up omitted-point RMSE relative to exact interpolants but produces a meaningfully smaller and more stable stored artifact,
3. notebook 03 showed that the broader spline direction still matters, but the custom implementation may not be the most useful way to pursue it.

So the comparison question is no longer "did the custom spline work at all?" It did. The useful question is what each method family is actually good for, and which branch remains worth carrying forward.

## Exact interpolants versus compact representations

### MRST-PCHIP and related exact methods

Barker and McDougall (2020) solve an interpolation problem. Their concern is reconstructing values between observed profile levels while preserving physically realistic structure, especially in SA-CT space. The full observed profile remains part of the object being queried.

That matters because exact interpolants and compact representations are not trying to optimize the same thing.

- Exact interpolants such as PCHIP, MR-PCHIP, and MRST-PCHIP prioritize reconstruction fidelity between retained observations.
- Compact spline artifacts prioritize storing a smaller queryable object that summarizes profile structure without retaining every original point.

Notebook 02 now makes this tradeoff concrete: exact interpolants win on omitted-point RMSE, while the custom compact artifact wins on artifact size and footprint stability.

### What exact interpolants still do better

The strongest exact-interpolant advantage is straightforward: they are better aligned with the task "predict the omitted observed value from the remaining observed values." That is exactly why PCHIP remains the stronger comparator when the target metric is withheld-point reconstruction RMSE.

This is also why notebook 03 keeps PCHIP in view even after the custom spline comparison. PCHIP still occupies the low-RMSE end of the tradeoff frontier.

### What compact representations still do differently

Notebook 02 supports a narrower but still meaningful claim for compact representations:

- they can produce materially smaller serialized artifacts,
- their footprint may vary less across profiles,
- they can carry explicit reconstruction and sensor-error metadata as part of the stored object,
- they remain queryable after the raw profile is discarded.

Those advantages do not make them superior interpolants. They make them plausible candidates for a different systems role.

## The custom curvature-adaptive spline prototype

### What the prototype established

The custom curvature-adaptive spline remains important in the research story because it demonstrated three things:

1. a per-cycle compact spline artifact can be made to work coherently on Argo data,
2. a non-exact fit can yield interpretable uncertainty fields and plausible residual structure,
3. a compact artifact can survive a comparison against exact interpolants as a real tradeoff rather than collapsing immediately.

Notebook 01 and notebook 02 are enough to preserve that branch as a serious exploration rather than a false start.

### What the prototype did not establish

The custom method did not establish that curvature-guided knot placement is the best way to pursue compact representation. That stronger claim is exactly what notebook 03 puts pressure on.

After notebook 03, the main open issue is not whether the custom spline has any merit. It does. The issue is whether its extra machinery buys enough over simpler native spline alternatives to justify remaining the center of the project.

### Relation to Li et al. (2005)

Li et al. (2005) remains a useful cross-domain analogue for why the custom prototype was a reasonable branch to explore:

- noisy observations,
- mixed flat and high-curvature structure,
- adaptive knot allocation,
- least-squares fitting instead of exact interpolation.

That analogue supports the plausibility of the prototype. It does not by itself support keeping the prototype as the live project default once simpler alternatives appear to cover the same tradeoff more directly.

## Native spline-family alternatives

Notebook 03 changed the method-comparison landscape by separating two questions that had previously been entangled:

1. is a non-exact spline-family representation still interesting?
2. does that require the custom curvature-adaptive implementation?

The answer now appears to be:

- yes to the first question,
- probably no to the second.

That is the most important comparison outcome to preserve in this note.

### Why the native spline path matters

The native spline path keeps the broad spline-family value proposition alive:

- continuous queryable representation,
- explicit fidelity-versus-footprint control through a smoothing parameter,
- compatibility with the uncertainty-aware representation story,
- substantially less method-specific machinery to justify.

If those properties survive while the custom method does not clearly outperform them, then the native spline path becomes the cleaner research direction.

## Yarger et al. (2022) and the representation problem

Yarger et al. remain important because they provide the clearest reviewed example of treating Argo profiles as continuous functions rather than fixed-level vectors. That larger framing still survives the custom-method decision.

What changed is the local interpretation of how this project extends that idea:

- earlier, the project could plausibly be read as pushing Yarger's vertical step toward custom profile-adaptive knot placement;
- now, the stronger reading is that the project is exploring compact single-profile representation and uncertainty outside the full spatiotemporal framework, while remaining open about which spline implementation best serves that role.

So Yarger still supports the representation direction. Notebook 03 mainly weakens the case for tying that direction specifically to the custom curvature-adaptive implementation.

## Current takeaway

The comparison story is now:

- exact interpolants remain the right reference class for pure reconstruction accuracy,
- the custom curvature-adaptive spline remains a valid and informative historical prototype,
- the broader spline-family direction still matters because compact tunable representations remain interesting,
- the current research center of gravity has shifted from custom knot heuristics toward simpler native spline methods plus uncertainty-aware profile encoding.

That is the comparison frame the rest of the topic should now assume unless a future notebook reopens the custom method on new evidence.
