# Inference Pipeline Strategy — Vietnam Disaster Prediction (v2)

Companion to `training_plan.md` ,`feature_engineering_plan.md` and rules from `disaster_rules.md`. Consumes the `ml-service/models/*.pkl` artifacts from `training.py`. Produces the required `{forecast, disasters}` JSON, serve-consistent with training.

**v2 changes:** (1) §3 validity gate now has a **demo bypass toggle**;
(2) §5 rule thresholds replaced with the legal definitions from **Quyết định
18/2021/QĐ-TTg**; (3) §4 titles mapped to the decree's official taxonomy;
(4) new §7 — risk-level (cấp độ 1–5) classification, with an explicit
computable-vs-not line.

---

## 0. Output Contract

```json
{
  "mode": "production",
  "forecast":  [ { "title": "<vi>", "probability": <int 0-100> }, ... ],
  "disasters": [ { "title": "<vi>", "probability": <int 0-100> }, ... ]
}
```

- `mode` is `"production"` or `"demo"` (§3): `"demo"` appears only when an
  unvalidated ML cell was surfaced (`FORCE_ML`). `AUTO` and `FORCE_RULE` both read
  `"production"`. Additive key — ignore for the strict two-array shape, or use it
  to drive a UI "DEMO" banner.
- `probability` is an integer percent; its meaning depends on the source:

| Item source                      | `probability` means                                     | Calibrated?        |
| -------------------------------- | --------------------------------------------------------- | ------------------ |
| ML cell (day3, gate ON)          | calibrated hazard probability                             | yes                |
| Baseline-rule / gated-off cell   | rule confidence (fired → rule precision; else base rate) | no                 |
| Rule hazard (heat/cold/fog, §5) | ensemble-agreement fraction (§6)                         | no (deterministic) |
| Forecast condition               | ensemble agreement across Open-Meteo models               | no                 |

Optional richer schema (recommended): add `"level": 1-5` per §7 and `"source"`
so the UI can style a calibrated 90% differently from a rule-based 90%.

---

## 1. Architecture — Two Producers, One Assembler

- **Disasters producer** = ML cells (calibrated, gated) ∪ rule-based hazards
  (heat/cold/fog) with QĐ-18 thresholds.
- **Forecast producer** = deterministic weather-condition classification, with
  probability from multi-model ensemble agreement (§6).

Keeping ML and rules in separate producers is what lets the demo toggle (§3)
affect only the ML side while the deterministic side stays untouched.

---

## 2. Serving-Time Feature Pipeline (parity)

Non-negotiable — calibrated probabilities are meaningless without it.

- Pull serving features from the **live Forecast API** at the Day-3 / Day-7
  horizon (matches each cell's training lead).
- Run the **same** `feature_engineering_plan.md` transforms.
- Load fitted objects from the artifact (encoders, sigmoid calibrator, frozen
  threshold, routed feature list) — never re-fit on live data.
- Assert served feature names == `artifact["features"]`, same order. Mismatch is
  a silent correctness bug.

**Required artifact fields:** `kind` ("model"|"baseline"), `calibrator`,
`threshold`, `features`, `rule`, `serve_enabled` (§3), `headline_test_block`,
and for baseline cells `rule_precision` + `base_rate`.

---

## 3. Per-Cell Source Resolution — Auto Fallback + Manual Override

The rule-based layer is the **fallback / safety layer**. Each cell resolves to one
of two sources — ML or rule — under three modes:

- **`AUTO` (production default):** serve the ML probability if the cell passes its
  validity gate; **the rule-based model auto-activates when ML performance is too
  low.** This is the production safety behavior.
- **`FORCE_RULE` (manual enable):** always serve the rule-based output, regardless
  of the ML gate. This is the operator override — use it for demos where you want
  clean, decree-grounded output, or in production if you decide to trust rules
  over a shaky model for a given cell.
- **`FORCE_ML` (gate bypass):** always serve the ML output even if it fails the
  gate. Diagnostic / "show the raw model" mode. Marks output `unvalidated`.

```python
from enum import Enum
class Mode(str, Enum):
    AUTO = "auto"            # production: ML if gate passes, else rule
    FORCE_RULE = "rule"      # manual: always rule-based (demo / ops override)
    FORCE_ML = "ml"          # diagnostic: always ML, gate bypassed

SERVE_CONFIG = {
    "mode": Mode.AUTO,       # PRODUCTION DEFAULT
    "roc_auc_floor": 0.55,
}

def compute_serve_enabled(metrics):        # bake into artifact at train time
    return (metrics["pr_auc"] > metrics["baseline_pr_auc"]
            and metrics["roc_auc"] >= SERVE_CONFIG["roc_auc_floor"])

def _serve_ml(artifact, X):
    p = float(artifact["calibrator"].predict_proba(X)[:, [1]])
    return {"probability": p, "calibrated": True,
            "alert": p >= artifact["threshold"]}

def _serve_rule(artifact, X):
    fired = bool(artifact["rule"](X))
    p = artifact["rule_precision"] if fired else artifact["base_rate"]
    return {"probability": p, "calibrated": False, "alert": fired}

def infer_cell(artifact, X_serve, cfg):
    is_model = artifact["kind"] == "model"
    gate_ok  = is_model and artifact["serve_enabled"]
    mode = cfg["mode"]

    # decide source
    if mode == Mode.FORCE_RULE or not is_model:
        out, src, unvalidated = _serve_rule(artifact, X_serve), "rule", False
    elif mode == Mode.FORCE_ML:
        out, src, unvalidated = _serve_ml(artifact, X_serve), "ml", (not gate_ok)
    else:  # AUTO
        if gate_ok:
            out, src, unvalidated = _serve_ml(artifact, X_serve), "ml", False
        else:                                   # ML too weak -> rule auto-activates
            out, src, unvalidated = _serve_rule(artifact, X_serve), "rule", False
    out["source"], out["unvalidated"] = src, unvalidated
    return out
```

Invariants:

- **`AUTO` never emits an ML probability from a cell below the floor** — the rule
  layer auto-activates for it. This is the production guarantee.
- **`FORCE_RULE` is safe to demo with** — every item is decree-grounded rule
  output, nothing unvalidated. Recommended demo mode when you want the product to
  look trustworthy rather than to show model internals.
- **`FORCE_ML` is the only mode that can surface an unvalidated ML number.** Reserve
  it for diagnostics; when any cell is unvalidated the envelope reads `mode: "demo"`
  and those items carry `unvalidated: true` so the UI can badge them.
- Until Previous Runs API is wired, day7 ML cells fail the gate: `AUTO` and
  `FORCE_RULE` both serve rules for them; only `FORCE_ML` shows the broken model.

---

## 4. Titles — Official Taxonomy (QĐ 18/2021, Điều 3)

```python
# ML-modeled hazards -> official decree names
DISASTER_TITLES_VI = {
    "y_lu_lut":   "Ngập lụt",      # inundation (Điều 45). CONFIRM vs "Lũ" (river) / "Lũ quét" (flash)
    "y_sat_lo":   "Sạt lở đất",    # landslide/subsidence from rain-flood (Điều 46)
    "y_dong_loc": "Lốc, sét",      # squall/whirlwind + lightning (Điều 52 group)
    "y_mua_da":   "Mưa đá",        # hail (Điều 52 group) — ships as baseline rule
    "y_mua_lon":  "Mưa lớn",       # heavy rain (Điều 44)
}

# Rule-based hazards (no model), official names
RULE_HAZARDS_VI = {
    "nang_nong": "Nắng nóng",       # Điều 47
    "ret_hai":   "Rét hại",         # Điều 53
    "suong_mu":  "Sương mù",        # Điều 51 (needs visibility data — see §5)
}
```

Two taxonomy notes:

- `y_dong_loc` maps to **local squall/whirlwind** (Điều 52), **not** tropical
  cyclone "Bão" (Điều 42). Bão is a separate official category you have no model
  for; source it from official storm bulletins / basin forecasts, not these cells.
- Confirm the `y_lu_lut` mapping — the decree separates Lũ (river flood), Ngập lụt
  (inundation), and Lũ quét (flash flood), each with different risk logic (§7).

---

## 5. Rule Thresholds — Legal Definitions (QĐ 18/2021, Điều 5)

Replaces the v1 placeholders. These are the decree's detection thresholds — a
hazard "is occurring" when the forecast crosses them over the target window.

```python
# Điều 5 — hazard onset definitions
QD18 = {
    "mua_lon_mm_24h":    50,        # > 50 mm/24h  = Mưa lớn
    "mua_to_mm_24h":    (50, 100),  #   50–100     = Mưa to
    "mua_rat_to_mm_24h": 100,       # > 100        = Mưa rất to
    "nang_nong_tmax_c":  35,        # Tmax(day) > 35°C = Nắng nóng
    "ret_hai_tavg_c":    13,        # Tavg(day) < 13°C = Rét hại
    "suong_mu_vis_m":    1000,      # visibility < 1 km (NO Open-Meteo variable)
    "song_lon_m":        2,         # waves ≥ 2 m
}

# Wind is defined in Beaufort "cấp gió", not m/s — convert first.
# ATNĐ: cấp 6–7 | Bão: ≥8 | Bão mạnh: 10–11 | rất mạnh: 12–15 | siêu bão: ≥16
_BEAUFORT_MS = [0.3,1.6,3.4,5.5,8.0,10.8,13.9,17.2,20.8,24.5,
                28.5,32.7,37.0,41.5,46.2,51.0]   # lower bound of cấp = index

def wind_to_cap(ms):
    cap = 0
    for i, lo in enumerate(_BEAUFORT_MS):
        if ms >= lo:
            cap = i
    return cap        # request Open-Meteo wind in m/s, feed gust for onset checks
```

Threshold-to-hazard checks (over the target window):

```python
def is_mua_lon(fc):    return fc.precip_24h_max   >  QD18["mua_lon_mm_24h"]
def is_nang_nong(fc):  return fc.tmax_day         >  QD18["nang_nong_tmax_c"]
def is_ret_hai(fc):    return fc.tavg_day         <  QD18["ret_hai_tavg_c"]
def is_dong_loc(fc):   return wind_to_cap(fc.gust_ms_max) >= 8   # squall proxy
```

**Fog stays unsolved:** the legal definition is visibility < 1 km, and Open-Meteo
has no visibility variable. Keep the near-saturation + low-wind proxy
(`temp_dew_spread ≈ 0` and `wind < 2 m/s`) but label it low-confidence, or drop
`suong_mu` until you add a visibility source. Do not claim it meets Điều 5.

---

## 6. Ensemble-Agreement Probability (forecast[] + rule hazards)

A single deterministic forecast has no probability. Poll multiple Open-Meteo
models for the same window; probability = fraction that agree.

```python
MODELS = ["ecmwf_ifs025", "gfs_seamless", "icon_seamless", "jma_seamless"]

def condition_probability(condition_fn, location, window, models=MODELS):
    hits = sum(int(condition_fn(open_meteo_forecast(location, window, model=m)))
               for m in models)
    return hits / len(models)     # ×100 for the contract
```

This gives the `90`/`100`-style values a real meaning (model agreement), not a
hard-coded confidence. Single-model fallback: `100` if the condition holds, item
omitted otherwise.

---

## 7. Risk-Level Classification (cấp độ 1–5) — NEW, optional

QĐ-18 (Điều 4, Chương III) grades every hazard on a 5-level scale with fixed map
colors. For a warning UI this is more actionable than a bare probability.

```python
CAP_DO = {
    1: {"label": "Rủi ro thấp",       "rgb": (175, 225, 255)},  # xanh dương nhạt
    2: {"label": "Rủi ro trung bình", "rgb": (250, 245, 140)},  # vàng nhạt
    3: {"label": "Rủi ro lớn",        "rgb": (255, 165,   0)},  # da cam
    4: {"label": "Rủi ro rất lớn",    "rgb": (255,   0,   0)},  # đỏ
    5: {"label": "Thảm họa",          "rgb": (128,   0, 128)},  # tím
}
# Điều 4 escalation: 2+ concurrent hazards -> +1 level;
# risk of serious loss of life/property -> up to +2 (cap at 5).
```

### What Open-Meteo can and cannot supply

| Risk input                                             | Source                         | From Open-Meteo?                |
| ------------------------------------------------------ | ------------------------------ | ------------------------------- |
| Intensity (mm/24h, Tmax, Tavg, wind cấp)              | point forecast                 | **yes**                   |
| Duration (days)                                        | multi-day forecast aggregation | **yes**                   |
| Region (Bắc Bộ / Trung Bộ / Tây Nguyên / Nam Bộ) | static per location            | yes (static map)                |
| Spatial extent (số huyện/xã affected)               | multi-location aggregation     | only if you aggregate locations |
| Risk zone (Thấp/TB/Cao/Rất cao), khu vực 1–4       | Phụ lục XII zone maps        | **no** — external layer  |
| River warning level (BĐ1/2/3)                         | hydrological stations          | **no** — external feed   |

So: **intensity + duration → provisional cấp độ** is computable now. Area, zone,
and river terms need external layers — until then, classify from intensity/
duration and mark the level `provisional`.

### Worked reference — Nắng nóng (Điều 47), transcribed from the decree

```python
# (tmin_c, tmax_c, day_min, day_max, {regions}, level)
# regions: BB=Bắc Bộ, TB=Trung Bộ, TN=Tây Nguyên, NB=Nam Bộ
# Boundary note: "từ X" = >=X ; "trên X" = >X. Verify edges against Điều 47.
NANG_NONG_RULES = [
    (35, 37,  3, 1e9, {"BB","TB","TN","NB"}, 1),
    (37, 39,  3,  25, {"BB","TB"},           1),
    (37, 39,  3,  10, {"TN","NB"},           1),
    (39, 41,  3,   5, {"BB","TB"},           1),
    (41, 1e9, 3,   5, {"TB"},                1),
    (37, 39, 10,  25, {"TN","NB"},           2),
    (37, 39, 25, 1e9, {"BB","TB"},           2),
    (39, 41,  3,  10, {"TN","NB"},           2),
    (39, 41,  5,  25, {"BB","TB"},           2),
    (41, 1e9, 3,  10, {"BB"},                2),
    (41, 1e9, 3,   5, {"TN","NB"},           2),
    (41, 1e9, 5,  10, {"TB"},                2),
    (37, 39, 25, 1e9, {"TN","NB"},           3),
    (39, 41, 10,  25, {"TN","NB"},           3),
    (39, 41, 25, 1e9, {"BB","TB"},           3),
    (41, 1e9, 5,  10, {"TN","NB"},           3),
    (41, 1e9,10,  25, {"BB","TB"},           3),
    (39, 41, 25, 1e9, {"TN","NB"},           4),
    (41, 1e9,10, 1e9, {"TN","NB"},           4),
    (41, 1e9,25, 1e9, {"BB","TB"},           4),
]

def classify_nang_nong(tmax_c, duration_days, region):
    level = 0
    for lo, hi, d0, d1, regs, lv in NANG_NONG_RULES:
        if lo <= tmax_c < hi and d0 <= duration_days <= d1 and region in regs:
            level = max(level, lv)
    return level or None
```

- **Mưa lớn (Điều 44):** bands 100–200 / 200–400 / >400 mm/24h × duration ×
  area. Encode the same tuple pattern; the area term needs multi-location
  aggregation (§7 table).
- **Rét hại (Điều 53):** Tavg bands 8–13 / 4–8 / 0–4 / <0 °C × duration × region
  (đồng bằng vs vùng núi Bắc Bộ). Same pattern.
- **Lũ quét / Sạt lở (Điều 46):** 24h rain + antecedent rain × **risk zone**
  (Thấp/TB/Cao/Rất cao) × khu vực 1–4. The risk-zone term is exactly the static
  terrain layer recommended in `training_plan.md` §2 — wire that layer in and this
  becomes computable; it also gives a physical cross-check against the ML cell.

Transcribe the remaining tables directly from the decree and unit-test each
against its worked examples — do not trust the summaries above blindly.

---

## 8. Output Assembly (paste-ready → contract)

```python
def to_pct(p): return max(0, min(100, int(round(p * 100))))

def build_output(location, horizon, cfg=SERVE_CONFIG):
    X = serve_features(location, horizon)          # §2 parity
    win = window_of(horizon)
    disasters, any_unvalidated = [], False

    # 8a. ML cells — source resolved per §3 (AUTO / FORCE_RULE / FORCE_ML)
    for key, title in DISASTER_TITLES_VI.items():
        art = load_artifact(f"ml-service/models/{key}_{horizon}.pkl")
        out = infer_cell(art, X[art["features"]], cfg)
        any_unvalidated |= out["unvalidated"]
        item = {"title": title, "probability": to_pct(out["probability"])}
        # optional: item["level"] = classify_<hazard>(...); item["source"]=...
        disasters.append(item)

    # 8b. Rule hazards (Điều 5 thresholds, ensemble probability)
    for cond, title in RULE_HAZARDS_VI.items():
        p = condition_probability(HAZARD_FNS[cond], location, win)
        disasters.append({"title": title, "probability": to_pct(p)})

    # 8c. Forecast conditions
    forecast = []
    for cond, title in FORECAST_CONDITIONS_VI.items():
        p = condition_probability(CONDITION_FNS[cond], location, win)
        if p > 0:
            forecast.append({"title": title, "probability": to_pct(p)})

    # "demo" only when an unvalidated ML cell was surfaced (FORCE_ML).
    # FORCE_RULE stays "production": rule output is decree-grounded, not unvalidated.
    mode = "demo" if any_unvalidated else "production"
    return {"mode": mode, "forecast": forecast, "disasters": disasters}
```

Final array items keep the required `{title, probability}` shape; `mode` and any
`level`/`source` are additive.

**Display decision to confirm:** show all monitored hazards every run (full board,
low probabilities included) vs filter to `alert == True`. Your example lists
several at once → default returns all; filter downstream if desired.

---

## 9. Serving Mechanics

- **Batch precompute, not on-demand.** Run `build_output` on a schedule aligned to
  Open-Meteo refresh, per `location_id`, write to a store, serve API from cache.
  Respects the ~10k req/day free tier (batch per refresh, not per user).
- **Emit both horizons** as separate JSONs. Envelope `mode` handles demo state;
  in production, consider labeling the day7 board "3-day" only while its ML cells
  fall back to baseline.
- Batch nearby locations + all variables into one call per model.

---

## 10. Logging, Monitoring, Drift

- Log every served row: `location_id, issue_time, horizon, mode, served_features, raw_probability, calibrated_probability, level, alert`, and later the realized
  label. This is both the drift monitor and the next re-training set.
- Track production calibration (rolling Brier / reliability) — an offline
  calibrator drifts as the live forecast distribution shifts.

---

## 11. Open Decisions

1. **Demo mode choice** (§3) — for the product demo, pick `FORCE_RULE` (clean,
   decree-grounded, nothing unvalidated — recommended) vs `FORCE_ML` (shows the raw
   model, badged unvalidated). Also confirm `FORCE_ML` can only be set per-request,
   never as the production default.
2. **day7 exposure** (§3/§9) — ML auto-falls-back to rules until Previous Runs API;
   decide whether the day7 board is shown at all meanwhile.
3. **Flood mapping** (§4) — `y_lu_lut` = Ngập lụt vs Lũ vs Lũ quét; changes §7 logic.
4. **Risk-level rollout** (§7) — ship intensity+duration provisional cấp độ now, or
   wait for the zone/river/area layers to compute full levels.
5. **Fog** (§5) — add a visibility source or drop `suong_mu`.
6. **Ensemble model set** (§6) — which Open-Meteo models to poll.
