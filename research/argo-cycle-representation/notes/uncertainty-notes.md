# Uncertainty Notes: Argo Cycle Representation

These notes cover uncertainty decomposition, sensor-error conventions, and the storage/query implications of the method families discussed in this topic. Source-backed claims in this file should trace to [../literature-review.md](../literature-review.md). The quantitative interpretations below are local project analysis rather than literature claims.

## Why uncertainty still matters after notebook 03

Notebook 03 narrows the active method direction away from the custom curvature-adaptive spline and toward simpler native spline-family methods. That does not make the uncertainty story less important. It makes it more central.

The custom prototype originally bundled together three ideas:

1. compact representation,
2. non-exact spline fitting,
3. explicit per-profile uncertainty output.

Notebook 03 weakens the case for keeping the custom fitting machinery. It does not weaken the case for carrying forward a compact representation whose approximation error is made visible rather than hidden.

So the uncertainty question is now broader than the historical custom method:

- what parts of the uncertainty story belong to the representation problem itself,
- what parts were specific to the custom prototype,
- and how should those pieces survive if the project centers on a simpler spline-family implementation?

## Sensor-error conventions from the Argo sources

The source-backed sensor and QC conventions are summarized in [../literature-review.md](../literature-review.md). The main implications for this topic remain:

- for standard delayed-mode SBE profiles at 0 to 2000 dbar, `2.4` dbar is the relevant residual pressure uncertainty after drift correction,
- `0.002` C remains the canonical temperature accuracy term,
- delayed-mode salinity uncertainty is adjustment-dependent with a `0.01` PSU floor rather than a depth-varying source-provided field,
- suspected TNPD microleaker profiles with `PRES_ADJUSTED_ERROR = 20` dbar should be excluded from routine use rather than treated as ordinary delayed-mode profiles.

Those source terms are stable across the method comparisons. What changes is how the project chooses to combine them with representation error.

## The historical custom-prototype uncertainty model

Notebook 01 used a local uncertainty construction built from three components:

1. a per-cycle reconstruction residual term,
2. a fixed instrument/error term,
3. a pressure-gradient-propagated term.

That construction remains useful as a prototype because it made the uncertainty fields interpretable:

- reconstruction error represented how lossy the stored artifact was,
- sensor terms represented upstream measurement limits,
- the pressure-gradient term made uncertainty widen where the water column was structurally difficult.

This is still a good explanation of why the prototype looked scientifically legible. It should now be read as the uncertainty story attached to the historical custom branch, not automatically as the final uncertainty design for the project.

## What survives beyond the custom prototype

Even after the method shift in notebook 03, several uncertainty principles still appear worth keeping:

- compact non-exact profile representations should expose approximation error rather than pretending to be exact,
- uncertainty should widen in regions where local profile structure makes pressure or fit errors matter more,
- uncertainty should remain queryable as part of the stored artifact rather than treated as an external afterthought,
- sensor-error terms should remain tied to Argo QC conventions rather than free-floating tuning constants.

Those principles belong to the broader representation problem, not only to the custom spline implementation.

## Exact interpolants and uncertainty

The literature reviewed here does not provide a standalone per-profile uncertainty model for methods such as PCHIP, Akima, or MRST-PCHIP. That distinction still matters.

Exact interpolants can be stronger on omitted-point RMSE while still leaving an open systems question:

- if a method is exact at retained points or near-exact on withheld-point reconstruction,
- but produces no compact artifact-level uncertainty field,
- then it may still be a weaker fit for the specific representation role this project is targeting.

This is one reason notebook 03 does not simply end the project with "PCHIP wins." PCHIP wins a narrower metric contest. The broader representation-and-uncertainty question remains.

## Storage and query implications

The storage story also needs to be split into historical and current layers.

### Historical custom prototype

Notebook 02 showed that the custom compact artifact can be materially smaller and more stable in footprint than the exact-interpolant baselines. That result remains worth keeping because it established the existence of a real storage/query tradeoff.

### Current direction

After notebook 03, the more important storage question is no longer "how compact was the custom artifact?" It is "what compactness and footprint behavior can be obtained from simpler native spline-family representations as `s` changes?"

So older footprint figures tied to the custom method should now be treated as evidence that compact artifacts are possible, not as the final storage benchmark for the topic.

## Current uncertainty work that still matters

Given the current state of the topic, the highest-value next uncertainty tasks are:

1. decide which parts of the notebook 01 uncertainty decomposition should transfer directly to a native spline-family artifact,
2. test whether uncertainty widens appropriately as spline smoothing increases and RMSE worsens,
3. separate approximation uncertainty from upstream sensor-error terms more explicitly,
4. evaluate whether the uncertainty outputs remain useful once the custom method is no longer the main artifact.

That is now a better match to the notebook sequence than treating the notebook 01 uncertainty construction as the settled final design.

## Local implementation guards

### Data-loading assumptions

Implementation note: if the local data-loading layer aliases delayed-mode adjusted salinity into the working salinity field, the `DATA_MODE` column remains the key indicator. Verify the behavior of the specific client library in use before relying on that rule operationally.

```python
print(data["DATA_MODE"].value_counts())
rt_count = (data["DATA_MODE"] == "R").sum()
if rt_count > 0:
    print(f"Warning: {rt_count} real-time profiles with uncorrected PSAL")
```

### Guard for TNPD-flagged profiles

```python
data = data[data["PRES_ERROR"] < 10]
# PRES_ERROR == 2.4: standard or low-risk TNPD, safe to use
# PRES_ERROR == 20: suspected microleaker, unknown large negative drift, exclude
```
