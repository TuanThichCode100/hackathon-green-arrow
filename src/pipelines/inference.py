"""
Serving pipeline for docs/inference_plan.md (v2). Consumes models/*.pkl
artifacts from training.py, pulls live Open-Meteo forecasts with the exact
same feature_engineering.py transforms used at train time, and assembles the
`{mode, forecast, disasters}` JSON contract (plan §0).

Scope notes (read before trusting the output for anything beyond a demo):

- §7 risk-level (cap do): only `classify_nang_nong` is implemented, because
  it's the one hazard in docs/disaster_rules.md whose full legal table needs
  only inputs Open-Meteo can supply (Tmax, duration, region). Mua lon/ret hai/
  sat lo/lu lut/dong loc/mua da all require an area (so-huyen/xa), risk-zone,
  or river-station input this pipeline has no source for (see disaster_rules.md
  Chuong III and inference_plan.md §7's own capability table) -- their `level`
  is left `None` with the specific missing input named in a comment, rather
  than guessing at an area/zone assumption for legally-flavored content.
- §5 suong_mu (fog): Open-Meteo has no visibility variable. Kept as the
  documented low-confidence proxy (near-saturation + low wind), never claimed
  to meet the Dieu 5 definition.
- §6/§8c FORECAST_CONDITIONS_VI: the plan references this dict without ever
  defining it. The 3 conditions below are a best-effort placeholder derived
  from cloud cover / precipitation -- confirm the real taxonomy with product
  before shipping; this is the one part of this file that is my own addition
  rather than a transcription of the plan.
"""

import json
from datetime import datetime, timezone as dt_timezone
from enum import Enum
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from feature_engineering import engineer_features
from map_meteo_features import map_meteo_to_inference_schema
from preprocess import fetch_meteo_data, load_location_mapping
from training import DEFAULT_OUTPUT_DIR, HORIZONS

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEFAULT_SERVING_DIR = DATA_DIR / "serving"
DEFAULT_LOG_PATH = DATA_DIR / "serving_log.jsonl"

# ---------------------------------------------------------------------------
# §3 -- per-cell source resolution: AUTO fallback + manual override
# ---------------------------------------------------------------------------


class Mode(str, Enum):
    AUTO = "auto"  # production: ML if gate passes, else rule
    FORCE_RULE = "rule"  # manual: always rule-based (demo / ops override)
    FORCE_ML = "ml"  # diagnostic: always ML, gate bypassed


SERVE_CONFIG = {
    "mode": Mode.AUTO,  # PRODUCTION DEFAULT
}


def _serve_ml(artifact: dict, row: pd.Series) -> dict:
    X = pd.DataFrame([row[artifact["features"]]])
    p = float(artifact["calibrator"].predict_proba(X)[:, 1][0])
    return {"probability": p, "calibrated": True, "alert": bool(p >= artifact["threshold"])}


def _serve_rule(artifact: dict, row: pd.Series) -> dict:
    rule = artifact["rule"]
    threshold = rule["threshold"]
    if threshold is None:
        return {"probability": artifact["base_rate"], "calibrated": False, "alert": False}

    value = float(row[rule["feature"]])
    fired = value >= threshold if rule["direction"] == "high" else value <= threshold
    p = artifact["rule_precision"] if fired else artifact["base_rate"]
    return {"probability": p, "calibrated": False, "alert": bool(fired)}


def infer_cell(artifact: dict, row: pd.Series, cfg: dict = SERVE_CONFIG) -> dict:
    """Resolve one cell's serve source per plan §3. `row` must contain every
    name in `artifact["features"]` (see serve_features / §2 parity)."""
    is_model = artifact["kind"] == "model"
    gate_ok = is_model and artifact["serve_enabled"]
    mode = cfg["mode"]

    if mode == Mode.FORCE_RULE or not is_model:
        out, src, unvalidated = _serve_rule(artifact, row), "rule", False
    elif mode == Mode.FORCE_ML:
        out, src, unvalidated = _serve_ml(artifact, row), "ml", (not gate_ok)
    else:  # AUTO
        if gate_ok:
            out, src, unvalidated = _serve_ml(artifact, row), "ml", False
        else:  # ML too weak -> rule auto-activates
            out, src, unvalidated = _serve_rule(artifact, row), "rule", False
    out["source"], out["unvalidated"] = src, unvalidated
    return out


_ARTIFACT_CACHE: dict[tuple[str, str, str], dict] = {}


def load_artifact(disaster: str, horizon_name: str, models_dir: Path = DEFAULT_OUTPUT_DIR) -> dict:
    key = (str(models_dir), disaster, horizon_name)
    if key not in _ARTIFACT_CACHE:
        _ARTIFACT_CACHE[key] = joblib.load(models_dir / f"{disaster}_{horizon_name}.pkl")
    return _ARTIFACT_CACHE[key]


# ---------------------------------------------------------------------------
# §4 -- titles, official taxonomy (QD 18/2021, Dieu 3)
# ---------------------------------------------------------------------------

DISASTER_TITLES_VI = {
    "y_lu_lut": "Ngập lụt",  # Dieu 45. See docs/inference_plan.md §4 note on Lu/Ngap lut/Lu quet mapping
    "y_sat_lo": "Sạt lở đất",  # Dieu 46
    "y_dong_loc": "Lốc, sét",  # Dieu 52 group -- squall/lightning, NOT tropical cyclone "Bao" (Dieu 42)
    "y_mua_da": "Mưa đá",  # Dieu 52 group -- ships as baseline rule (feasibility gate)
    "y_mua_lon": "Mưa lớn",  # Dieu 44
}

RULE_HAZARDS_VI = {
    "nang_nong": "Nắng nóng",  # Dieu 47
    "ret_hai": "Rét hại",  # Dieu 53
    "suong_mu": "Sương mù",  # Dieu 51 -- low-confidence proxy, see module docstring
}

# Not part of the plan (see module docstring): best-effort placeholder only.
FORECAST_CONDITIONS_VI = {
    "nang": "Trời nắng",
    "nhieu_may": "Nhiều mây",
    "co_mua": "Có mưa",
}

# ---------------------------------------------------------------------------
# §5 -- QD18 rule thresholds (Dieu 5) + Beaufort conversion
# ---------------------------------------------------------------------------

QD18 = {
    "mua_lon_mm_24h": 50,  # > 50 mm/24h = Mua lon
    "mua_to_mm_24h": (50, 100),
    "mua_rat_to_mm_24h": 100,
    "nang_nong_tmax_c": 35,  # Tmax(day) > 35C = Nang nong
    "ret_hai_tavg_c": 13,  # Tavg(day) < 13C = Ret hai
    "suong_mu_vis_m": 1000,  # visibility < 1km -- NO Open-Meteo variable
    "song_lon_m": 2,
}

# Wind is defined in Beaufort "cap gio", not m/s -- convert first.
# ATND: cap 6-7 | Bao: >=8 | Bao manh: 10-11 | rat manh: 12-15 | sieu bao: >=16
_BEAUFORT_MS = [
    0.3, 1.6, 3.4, 5.5, 8.0, 10.8, 13.9, 17.2, 20.8, 24.5,
    28.5, 32.7, 37.0, 41.5, 46.2, 51.0,
]  # fmt: skip


def wind_to_cap(ms: float) -> int:
    cap = 0
    for i, lo in enumerate(_BEAUFORT_MS):
        if ms >= lo:
            cap = i
    return cap


def is_nang_nong(row: pd.Series) -> bool:
    return bool(row["temperature_max_24h"] > QD18["nang_nong_tmax_c"])


def is_ret_hai(row: pd.Series) -> bool:
    return bool(row["tavg_24h"] < QD18["ret_hai_tavg_c"])


def is_suong_mu(row: pd.Series) -> bool:
    """Fog stays unsolved (plan §5): Open-Meteo has no visibility variable.
    Near-saturation + low wind is a low-confidence proxy, not the Dieu 5
    definition (visibility < 1km) -- do not present this as decree-compliant."""
    return bool(row["temp_dew_spread_min_24h"] < 1.0 and row["wind_avg_24h"] < 2.0)


HAZARD_FNS = {"nang_nong": is_nang_nong, "ret_hai": is_ret_hai, "suong_mu": is_suong_mu}


def is_nang(row: pd.Series) -> bool:
    return bool(row["cloud_cover_max_24h"] < 30 and row["precip_24h_sum"] == 0)


def is_nhieu_may(row: pd.Series) -> bool:
    return bool(row["cloud_cover_max_24h"] >= 70 and row["precip_24h_sum"] == 0)


def is_co_mua(row: pd.Series) -> bool:
    return bool(row["precip_24h_sum"] > 0)


CONDITION_FNS = {"nang": is_nang, "nhieu_may": is_nhieu_may, "co_mua": is_co_mua}

# ---------------------------------------------------------------------------
# §2 -- serving-time feature pipeline (parity with training)
# ---------------------------------------------------------------------------

_MAPPING_DF = None


def _get_mapping_df() -> pd.DataFrame:
    global _MAPPING_DF
    if _MAPPING_DF is None:
        _MAPPING_DF = load_location_mapping()
    return _MAPPING_DF


def _rolling_by_location(df: pd.DataFrame, value_col: str, window: str, func: str) -> np.ndarray:
    """Same backward time-rolling idiom as feature_engineering._time_rolling,
    for the couple of aggregates (tavg_24h, wind_avg_24h, precip_24h_sum)
    the QD18 rule/forecast checks need but the ML feature set doesn't."""
    result = pd.Series(index=df.index, dtype="float64")
    for _, group in df.groupby("location_id"):
        result.loc[group.index] = group.set_index("time")[value_col].rolling(window).agg(func).to_numpy()
    return result.to_numpy()


def pull_engineered(location_name: str, horizon_name: str, model: str | None = None) -> pd.DataFrame:
    """Pull the live Open-Meteo forecast for `location_name` and run it
    through the identical feature_engineering transforms used in training.
    Returns the full engineered hourly series (serve_features picks the
    single target row from it; duration-based checks like §7's heat-streak
    need the whole series, not just one row).

    `model` pins one Open-Meteo model (§6 ensemble poll); the default (None)
    is the best-match ensemble used for the ML cells and rule hazards' primary
    reading (plan §2: "live Forecast API", not an ensemble average).
    """
    horizon_hours = HORIZONS[horizon_name]
    past_days = 10  # >= longest (168h) rolling window used in training, plus margin
    forecast_days = horizon_hours // 24 + 2  # covers the target day plus margin

    mapping_df = _get_mapping_df()
    raw = fetch_meteo_data(location_name, past_days=past_days, forecast_days=forecast_days, mapping_df=mapping_df, models=model)
    inference_df = map_meteo_to_inference_schema(raw).rename(columns={"location": "location_id"})
    engineered = engineer_features(inference_df)

    engineered["tavg_24h"] = _rolling_by_location(engineered, "temperature_2m", "24h", "mean")
    engineered["wind_avg_24h"] = _rolling_by_location(engineered, "wind_speed_10m", "24h", "mean")
    engineered["precip_24h_sum"] = _rolling_by_location(engineered, "precipitation", "24h", "sum")
    return engineered


def _select_target_row(engineered: pd.DataFrame, horizon_hours: int, location_name: str, horizon_name: str) -> pd.Series:
    target_tz = engineered["time"].dt.tz
    target_time = pd.Timestamp.now(tz=target_tz).floor("h") + pd.Timedelta(hours=horizon_hours)
    idx = (engineered["time"] - target_time).abs().idxmin()
    row = engineered.loc[idx]

    if abs((row["time"] - target_time).total_seconds()) > 3600:
        raise ValueError(
            f"Serving pull for {location_name!r}/{horizon_name} doesn't reach target time "
            f"{target_time} (closest available is {row['time']}) -- widen forecast_days."
        )
    return row


def serve_features(location_name: str, horizon_name: str, model: str | None = None) -> pd.Series:
    """The single engineered row nearest the target time (issue time +
    horizon) -- what the ML cells and single-row rule/condition checks serve
    from. See pull_engineered() for the full series."""
    engineered = pull_engineered(location_name, horizon_name, model)
    return _select_target_row(engineered, HORIZONS[horizon_name], location_name, horizon_name)


def _assert_feature_parity(artifact: dict, row: pd.Series) -> None:
    """Plan §2: mismatch between served and trained feature names is a silent
    correctness bug -- fail loudly instead."""
    missing = [f for f in artifact["features"] if f not in row.index]
    if missing:
        raise ValueError(f"Serving row is missing feature(s) {missing} required by artifact {artifact['disaster']!r}")


# ---------------------------------------------------------------------------
# §6 -- ensemble-agreement probability (forecast[] + rule hazards)
# ---------------------------------------------------------------------------

MODELS = ["ecmwf_ifs025", "gfs_seamless", "icon_seamless", "jma_seamless"]


def poll_ensemble_rows(location_name: str, horizon_name: str, models: list[str] | None = None) -> dict[str, pd.Series]:
    """One serve_features() pull per model, reused across every rule-hazard
    and forecast-condition check for that (location, horizon) -- plan §9:
    "batch ... all variables into one call per model", not one call per
    condition per model."""
    models = models if models is not None else MODELS
    rows = {}
    for m in models:
        try:
            rows[m] = serve_features(location_name, horizon_name, model=m)
        except Exception as exc:  # noqa: BLE001 -- one model's outage shouldn't sink the whole board
            print(f"  [ensemble] model {m!r} unavailable for {location_name!r}/{horizon_name}: {exc}")
    return rows


def condition_probability(condition_fn, ensemble_rows: dict[str, pd.Series]) -> float:
    if not ensemble_rows:
        return 0.0
    hits = sum(int(condition_fn(row)) for row in ensemble_rows.values())
    return hits / len(ensemble_rows)


# ---------------------------------------------------------------------------
# §7 -- risk-level (cap do 1-5) classification -- see module docstring scope note
# ---------------------------------------------------------------------------

CAP_DO = {
    1: {"label": "Rủi ro thấp", "rgb": (175, 225, 255)},
    2: {"label": "Rủi ro trung bình", "rgb": (250, 245, 140)},
    3: {"label": "Rủi ro lớn", "rgb": (255, 165, 0)},
    4: {"label": "Rủi ro rất lớn", "rgb": (255, 0, 0)},
    5: {"label": "Thảm họa", "rgb": (128, 0, 128)},
}

# (tmin_c, tmax_c, day_min, day_max, {regions}, level) -- transcribed from
# disaster_rules.md Chuong III.6 / Dieu 47, cross-checked against
# inference_plan.md §7's worked reference (they match).
NANG_NONG_RULES = [
    (35, 37, 3, 1e9, {"BB", "TB", "TN", "NB"}, 1),
    (37, 39, 3, 25, {"BB", "TB"}, 1),
    (37, 39, 3, 10, {"TN", "NB"}, 1),
    (39, 41, 3, 5, {"BB", "TB"}, 1),
    (41, 1e9, 3, 5, {"TB"}, 1),
    (37, 39, 10, 25, {"TN", "NB"}, 2),
    (37, 39, 25, 1e9, {"BB", "TB"}, 2),
    (39, 41, 3, 10, {"TN", "NB"}, 2),
    (39, 41, 5, 25, {"BB", "TB"}, 2),
    (41, 1e9, 3, 10, {"BB"}, 2),
    (41, 1e9, 3, 5, {"TN", "NB"}, 2),
    (41, 1e9, 5, 10, {"TB"}, 2),
    (37, 39, 25, 1e9, {"TN", "NB"}, 3),
    (39, 41, 10, 25, {"TN", "NB"}, 3),
    (39, 41, 25, 1e9, {"BB", "TB"}, 3),
    (41, 1e9, 5, 10, {"TN", "NB"}, 3),
    (41, 1e9, 10, 25, {"BB", "TB"}, 3),
    (39, 41, 25, 1e9, {"TN", "NB"}, 4),
    (41, 1e9, 10, 1e9, {"TN", "NB"}, 4),
    (41, 1e9, 25, 1e9, {"BB", "TB"}, 4),
]


def classify_nang_nong(tmax_c: float, duration_days: int, region: str) -> int | None:
    level = 0
    for lo, hi, d0, d1, regs, lv in NANG_NONG_RULES:
        if lo <= tmax_c < hi and d0 <= duration_days <= d1 and region in regs:
            level = max(level, lv)
    return level or None


def region_for_location(lat: float, lon: float, elevation: float | None = None) -> str:
    """Rough Bac Bo / Trung Bo / Tay Nguyen / Nam Bo bucketing from lat/lon.

    NOT an authoritative province lookup -- Vietnam's actual region boundaries
    don't follow clean latitude bands (Tay Nguyen in particular overlaps Nam
    Trung Bo's latitude range and is really an elevation/plateau distinction).
    Good enough for a provisional cap do; replace with a real province ->
    region join before relying on this for decree-compliance-grade output.
    """
    if lat >= 18.5:
        return "BB"
    if lat < 11.5:
        return "NB"
    if elevation is not None and elevation >= 400 and lon < 109.0:
        return "TN"
    return "TB"


def _consecutive_hot_days(engineered_df: pd.DataFrame, target_time: pd.Timestamp, tmax_threshold: float) -> int:
    """Count consecutive days (ending at target_time's date) whose daily max
    temperature clears `tmax_threshold`, using only the pulled forecast
    window -- undercounts a heatwave that started before `past_days` back."""
    daily_tmax = engineered_df.set_index("time")["temperature_2m"].resample("1D").max()
    streak = 0
    for date, tmax in daily_tmax.sort_index().items():
        if date.date() > target_time.date():
            break
        streak = streak + 1 if tmax > tmax_threshold else 0
    return streak


# ---------------------------------------------------------------------------
# §8 -- output assembly
# ---------------------------------------------------------------------------


def to_pct(p: float) -> int:
    return max(0, min(100, int(round(p * 100))))


def build_output(location_name: str, horizon_name: str, cfg: dict = SERVE_CONFIG) -> dict:
    """Assemble the `{mode, forecast, disasters}` contract for one location
    at one horizon (plan §8)."""
    horizon_hours = HORIZONS[horizon_name]
    engineered = pull_engineered(location_name, horizon_name)
    row = _select_target_row(engineered, horizon_hours, location_name, horizon_name)
    ensemble_rows = poll_ensemble_rows(location_name, horizon_name)

    disasters, any_unvalidated = [], False

    # 8a. ML cells -- source resolved per §3 (AUTO / FORCE_RULE / FORCE_ML)
    for key, title in DISASTER_TITLES_VI.items():
        artifact = load_artifact(key, horizon_name)
        _assert_feature_parity(artifact, row)
        out = infer_cell(artifact, row, cfg)
        any_unvalidated |= out["unvalidated"]
        disasters.append({"title": title, "probability": to_pct(out["probability"]), "source": out["source"], "level": None})

    # 8b. Rule hazards (Dieu 5 thresholds, ensemble probability)
    for key, title in RULE_HAZARDS_VI.items():
        p = condition_probability(HAZARD_FNS[key], ensemble_rows)
        item = {"title": title, "probability": to_pct(p), "source": "rule", "level": None}
        if key == "nang_nong" and p > 0:
            mapping_row = _get_mapping_df()
            match = mapping_row[mapping_row["commune_name"].str.strip().str.casefold() == location_name.strip().casefold()]
            if not match.empty:
                lat, lon = float(match.iloc[0]["latitude"]), float(match.iloc[0]["longitude"])
                elevation = float(match.iloc[0]["elevation"]) if "elevation" in match.columns else None
                region = region_for_location(lat, lon, elevation)
                duration = _consecutive_hot_days(engineered, row["time"], QD18["nang_nong_tmax_c"])
                item["level"] = classify_nang_nong(row["temperature_max_24h"], duration, region)
        disasters.append(item)

    # 8c. Forecast conditions (not in the plan verbatim -- see module docstring)
    forecast = []
    for key, title in FORECAST_CONDITIONS_VI.items():
        p = condition_probability(CONDITION_FNS[key], ensemble_rows)
        if p > 0:
            forecast.append({"title": title, "probability": to_pct(p)})

    # "demo" only when an unvalidated ML cell was surfaced (FORCE_ML).
    mode = "demo" if any_unvalidated else "production"
    return {"mode": mode, "forecast": forecast, "disasters": disasters}


# ---------------------------------------------------------------------------
# §9 -- serving mechanics (batch precompute)
# ---------------------------------------------------------------------------


def run_batch(
    location_names: list[str],
    horizon_names: tuple[str, ...] | None = None,
    output_dir: Path = DEFAULT_SERVING_DIR,
    cfg: dict = SERVE_CONFIG,
) -> list[dict]:
    """Batch precompute (plan §9): run build_output per (location, horizon),
    write each to its own JSON file rather than serving on-demand."""
    horizon_names = horizon_names if horizon_names is not None else tuple(HORIZONS.keys())
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for location_name in location_names:
        for horizon_name in horizon_names:
            try:
                output = build_output(location_name, horizon_name, cfg)
            except Exception as exc:  # noqa: BLE001 -- one location shouldn't sink the whole batch
                print(f"[run_batch] failed for {location_name!r}/{horizon_name}: {exc}")
                continue
            slug = location_name.strip().replace(" ", "_")
            out_path = output_dir / f"{slug}_{horizon_name}.json"
            out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
            results.append({"location": location_name, "horizon": horizon_name, "path": str(out_path), **output})
    return results


# ---------------------------------------------------------------------------
# §10 -- logging (drift monitoring / re-training set)
# ---------------------------------------------------------------------------


def log_served_row(location_name: str, horizon_name: str, output: dict, log_path: Path = DEFAULT_LOG_PATH) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "location": location_name,
        "horizon": horizon_name,
        "issue_time": datetime.now(dt_timezone.utc).isoformat(),
        **output,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    mapping = load_location_mapping()
    sample_location = mapping.iloc[0]["commune_name"]
    for horizon_name in HORIZONS:
        output = build_output(sample_location, horizon_name)
        log_served_row(sample_location, horizon_name, output)
        print(f"\n=== {sample_location} / {horizon_name} ===")
        print(json.dumps(output, ensure_ascii=False, indent=2))
