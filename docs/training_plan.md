# Model Training Plan — Vietnam Disaster Prediction (Open-Meteo Only)

Companion to `feature_engineering_plan.md`. Uses that document's feature set and
routing as-is. This plan covers everything from raw data sourcing to a
serving-consistent, leakage-free trained model.

**Design commitments (why this plan looks the way it does):**
- ERA5 / reanalysis is not available → all data comes from Open-Meteo.
- Train-serve consistency is enforced by sourcing training features from
  **forecast archives at the matched lead time**, not from observed history.
- Splits are temporal with an embargo ≥ the longest feature window, because
  random CV leaks through overlapping aggregation windows and autocorrelation.
- Models are **pooled across locations** (one model per disaster × horizon,
  with location + static features), because ~3–4 years of Open-Meteo archive
  gives too few positives for per-location models.

---

## 0. Data Source Mapping (Open-Meteo)

Three distinct Open-Meteo endpoints do three different jobs. Do not collapse them.

| Role | Endpoint | Why this one |
|------|----------|--------------|
| **Labels (ground truth)** | Historical Forecast API (initial/analysis hours) | Initial hours of each run are assimilated against observations — closest thing to "what actually happened" without ERA5. |
| **Training features** | Previous Runs API, `previous_day3` (72h model) and `previous_day7` (168h model) | Returns the value that *was forecast* 3 / 7 days ahead — same error profile as live serving. This is the whole point. |
| **Serving features** | Forecast API, Day-3 / Day-7 horizon | Live forecasts at inference. |

**Gating check before anything else:** confirm `previous_day7` archive depth at
your `location_id` set. If < ~2 years, per-location training is infeasible →
proceed with pooling (already the default here) and consider widening the target
window (§2) to raise positive counts.

**Do not** source training features from the Historical Forecast API's stitched
initial hours. Those are near-observed (short lead) and will make the model
over-trust its inputs — the exact mismatch this plan exists to avoid.

---

## 1. Label Construction — DECIDE FIRST

Pick one. The rest of the pipeline is identical either way; only `build_labels()`
changes.

**Option A — Physical proxy labels (default, self-contained).**
Derive each `y_*` from Historical Forecast API observed-quality variables via
physical thresholds, per location and target day. Example definitions (tune to
Vietnamese thresholds / your domain source):
- `y_lu_lut` (flood): 24h or 72h accumulated `precipitation` ≥ regional flood
  threshold, optionally gated on high `deep_soil_moisture`.
- `y_mua_lon` (heavy rain): 24h `precipitation` ≥ heavy-rain threshold.
- `y_dong_loc` (cyclone): `wind_gusts_10m` max ≥ threshold AND `surface_pressure`
  min below percentile.
- `y_mua_da` (hail): proxy only — instability signature; expect weak labels.
- `y_sat_lo` (landslide): rainfall-on-saturated-ground rule (accumulation +
  `deep_soil_moisture`), since Open-Meteo has no direct landslide signal.

Consequence: the model predicts *"conditions will cross a hazard threshold,"*
not *"an official disaster will be recorded."* State this explicitly in alerts.

**Option B — External event registry (better truth, more work).**
Use a disaster-event database (government bulletins / EM-DAT / curated news) and
spatially-temporally join events to `(location_id, target_day)`. Higher label
quality, but resolution-mismatch handling required (province-level events vs
point forecasts). Recommended as a later upgrade, or to *anchor/validate* the
Option A thresholds.

**Recommendation:** ship on A, calibrate the thresholds against whatever sparse
real events you can collect, migrate labels toward B over time. Lock the choice
now — it defines the target.

---

## 2. Sample Definition & Dataset Assembly

**Unit of a training example:** `(issue_time, location_id)`.
- **Features** = forecast issued at `issue_time` for the target window, pulled
  from Previous Runs at the matched lead (`day3` / `day7`), then run through the
  `feature_engineering_plan.md` pipeline (cyclical encoding, accumulations,
  pressure deltas, NWR, Landslide Trigger Index, feature crosses).
- **Label** = 1 if the disaster occurs in the target window
  `[issue_time + H, issue_time + H + W]`, else 0.
  - `H` = 72h or 168h (horizon).
  - `W` = target window width. Start at **24h**. Widen to 48h only if positive
    counts are too low — wider `W` raises recall-able base rate but blurs timing.

**Windowed target, not point-in-time:** never predict the exact hour. The label
is an *any-occurrence-in-window* indicator, matching the "preparation window" use
case.

**Static / geographic features (add these — biggest missing signal for
flood/landslide):**
- `elevation` (available from Open-Meteo).
- DEM-derived (SRTM/Copernicus, free, one-time): slope, aspect, upstream
  catchment area, distance-to-river. These are what let a pooled model tell
  location A (floods) from location B (doesn't) without memorizing the ID.
- `location_id` as a categorical is a weak substitute; include the terrain
  features if at all feasible.

**Feature routing:** apply the routing table from `feature_engineering_plan.md`
as specified. One diagnostic caveat: also train an "all-features" variant per
cell as an ablation — boosted trees regularize irrelevant features via
`colsample`, and routing can sever real cross-domain signal (pressure/wind do
predict floods via the storm system). Keep routing only where the ablation shows
it helps.

**Assembled matrix:** one long table keyed by `(issue_time, location_id)` with
engineered features + static features + the five label columns. Build it once for
each horizon (`day3`, `day7`) since the feature source differs by lead.

---

## 3. Temporal Splitting (the leakage fix)

**Walk-forward (expanding-window) CV, split by `issue_time`, with an embargo.**

```
|=== train ===|  [embargo]  |= cal =|  [embargo]  |= test =|  → step forward
```

- **Embargo ≥ 7 days** (longest feature aggregation window). Use **10 days** for
  margin. No feature window on either side of a boundary may overlap the other
  split's period. This is non-negotiable — without it, offline PR-AUC is fiction.
- Split by **issue_time**, never by target_day, and never randomly.
- Per fold, three temporally-ordered blocks: **train → calibrate+threshold →
  test**. Calibration and threshold selection *must* come from the block after
  training and before test (§5). Reusing training data for either reintroduces
  leakage.
- Report metrics aggregated across all walk-forward test blocks, plus the final
  most-recent block as the headline (closest to production conditions).

**Pooling note:** locations are pooled into each fold, but the *time* split is
global — the same `issue_time` boundary applies to all locations, so no location
leaks its own future.

---

## 4. Per-Cell Feasibility Gate

Before training any of the 10 (5 disasters × 2 horizons) cells, count positives.

```python
for disaster, horizon in cells:
    n_pos = labels[disaster][horizon].sum()
    n_tot = len(labels[disaster][horizon])
    base_rate = n_pos / n_tot
    # Gate:
    #   n_pos < ~150 total  -> ML unreliable; use a physical threshold rule instead
    #   n_pos in [150, 500] -> train, but expect high variance; sigmoid calibration only
    #   n_pos > 500         -> full pipeline OK
```

Expected outcome: **flood / landslide / heavy-rain cells clear the bar;
hail and 168h-cyclone likely do not** (§7). Don't spend equal effort on all 10 —
route effort by feasibility, and fall back to a documented physical-threshold
rule for cells that fail the gate.

---

## 5. Model Configuration

**One XGBoost classifier per surviving cell.** Starting hyperparameters for rare-
event tabular (tune per cell via the walk-forward folds, not a random search on
pooled data):

```python
params = dict(
    objective="binary:logistic",
    eval_metric="aucpr",          # optimize PR-AUC, not logloss/auc
    max_depth=4,                  # shallow: few positives, avoid overfit
    min_child_weight=5,           # raise if positives are scarce
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=2.0,
    reg_alpha=0.5,
    learning_rate=0.03,
    n_estimators=2000,            # cap via early stopping on the cal block
    tree_method="hist",
)
# Imbalance: tie weight to the fold's class ratio.
scale_pos_weight = n_neg / n_pos   # computed on the TRAIN block only
# Alternative for extreme skew: custom focal-loss objective instead of s_p_w.
```

- **Early stopping** on the calibration block's `aucpr`, ~100-round patience.
- Compute `scale_pos_weight` from the **train block only** — recomputing on the
  full dataset leaks base-rate info across the split.
- If a focal-loss objective is used, drop `scale_pos_weight` (don't stack both).

**Calibration:**
- Fit on the **calibration block** (post-train, pre-test), never on train.
- **Use sigmoid (Platt) scaling by default**, not isotonic. Isotonic is
  nonparametric and data-hungry; with rare-event positive counts it overfits the
  calibration set. Switch a specific cell to isotonic only if that cell has
  >1000 positives.
- Report **Brier score + reliability curve** on the test block so "15% calibrated
  probability" actually means 15%.

**Threshold selection:**
- Choose the operating threshold from the **calibration block's PR curve**, not
  the test block (selecting on test leaks).
- Target an F2/F3-optimal point, or the min threshold achieving a recall floor
  you set for public safety (e.g. recall ≥ 0.8), whichever your policy prefers.
- Freeze the threshold; evaluate it untouched on test.

---

## 6. Evaluation Protocol

**Primary metrics (all on held-out test blocks):**
- **PR-AUC** — headline, threshold-independent.
- **F2 / F3** at the frozen threshold — recall-weighted.
- **Event-based recall with tolerance** — did an alert fire for the right
  `(province, window)`? Point-exact scoring understates a preparation system's
  value; allow spatial (province) and temporal (±window) tolerance.
- **Brier + reliability** — calibration quality.

**Mandatory baselines — the model must beat these or it isn't worth shipping:**
1. Climatological base rate (predict seasonal frequency).
2. **Single-feature physical threshold** (e.g. alert when `precip_7d_sum`
   exceeds a percentile). This is the real bar. If XGBoost doesn't beat a one-
   line rule, ship the rule.

**Do not report** raw accuracy or ROC-AUC as headline numbers — under this
imbalance the huge true-negative count swamps the FPR denominator, so ROC-AUC can
look strong while precision at your operating point is poor.

---

## 7. Physical Skill Ceiling — Set Expectations Per Cell

Not all 10 cells are equally learnable, regardless of pipeline quality:

- **Tractable at 72h and 168h:** floods, landslides, heavy rain — accumulation-
  driven, integrate slowly, forecastable at long lead.
- **Weak at 168h:** cyclone intensity/track — better sourced from operational
  basin forecasts (JMA/JTWC) than reconstructed from point features.
- **Weak at any lead:** hail — localized convective, beyond deterministic NWP
  skill; the model will largely learn seasonal climatology. Treat as low-
  confidence / advisory, or descope.

Build order: **flood-72h and heavy-rain-72h first** (highest signal, validates the
whole pipeline), then landslide, then the 168h variants, then decide whether
cyclone/hail cells clear the feasibility gate at all.

---

## 8. Reference Training Loop (per cell)

```python
def train_cell(disaster, horizon, df):
    feats = route_features(disaster, ALL_FEATURES)   # per feature_engineering_plan
    folds = walk_forward_splits(df.issue_time, embargo="10D",
                                blocks=("train", "cal", "test"))
    results = []
    for train_idx, cal_idx, test_idx in folds:
        Xtr, ytr = df.loc[train_idx, feats], df.loc[train_idx, disaster]
        Xca, yca = df.loc[cal_idx,   feats], df.loc[cal_idx,   disaster]
        Xte, yte = df.loc[test_idx,  feats], df.loc[test_idx,  disaster]

        spw = (ytr == 0).sum() / max((ytr == 1).sum(), 1)
        model = XGBClassifier(**params, scale_pos_weight=spw)
        model.fit(Xtr, ytr, eval_set=[(Xca, yca)],
                  early_stopping_rounds=100, verbose=False)

        calib = CalibratedClassifierCV(model, method="sigmoid", cv="prefit")
        calib.fit(Xca, yca)                       # calibrate on cal block

        thr = pick_threshold_from_pr(calib.predict_proba(Xca)[:, 1], yca,
                                     target="F2")  # threshold from cal block
        results.append(evaluate(calib, thr, Xte, yte, baselines=True))
    return aggregate(results), refit_final_on_all_but_holdout(...)
```

- Final production model: refit on all data up to a frozen recent holdout, carry
  the frozen threshold, persist the calibrator with the model.

---

## 9. Serving Parity (do not skip)

The serving path must reproduce the training feature computation exactly:
- Serving features come from the **live Forecast API** at Day-3 / Day-7 horizon,
  passed through the **identical** `feature_engineering_plan.md` transforms.
- Any transform fit on training data (scalers, encoders, thresholds, calibrator)
  is **persisted and loaded at serve time** — never recomputed on live data.
- Log served features + predicted probability + realized label for every alert,
  to build the drift-monitoring and re-training set.

---

## 10. Open Decisions (blocking / near-blocking)

1. **Label source** (§1) — A vs B. Blocking; defines the target.
2. **Previous Runs archive depth** (§0) — determines pooling and window width.
   Blocking for data volume.
3. **Target window `W`** — 24h default; widen only if positives are too sparse.
4. **Regional physical thresholds** for proxy labels and for the baseline rule —
   needs a domain/meteorological source for Vietnam.
5. **Static terrain features** — elevation-only vs full DEM derivatives; the
   latter meaningfully lifts flood/landslide skill.
