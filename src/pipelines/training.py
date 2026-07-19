"""
Trains the pooled, per-(disaster, horizon) XGBoost classifiers described in
docs/training_plan.md: windowed any-occurrence labels, walk-forward temporal
splitting with an embargo, sigmoid calibration, PR-curve threshold selection,
and evaluation against the mandatory climatological / single-feature baselines.

Known interim limitation (plan §0 / §10 item 2): the plan calls for sourcing
training features from the Open-Meteo *Previous Runs* API at the matched lead
(previous_day3 / previous_day7), so training features carry the same forecast
error as serving. That endpoint isn't wired into the pipeline yet -- the only
assembled dataset is data/weather_features_engineered.csv (built from the
Historical Forecast API via feature_engineering.py). Until Previous Runs is
available, both horizons here reuse that same feature series; only the label's
lead time (`horizon_hours`) differs between cells. Swap in the per-horizon
Previous Runs dataframe here once it exists -- the rest of the pipeline (label
windowing, splitting, training, calibration) does not need to change.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import average_precision_score, brier_score_loss, precision_recall_curve, roc_auc_score
from xgboost import XGBClassifier

from pipelines.feature_engineering import FEATURE_ROUTING
from pipelines.map_meteo_features import TRAINING_LABEL_COLUMNS

DEFAULT_FEATURES_PATH = Path(__file__).resolve().parents[2] / "data" / "weather_features_engineered.csv"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "models"

DISASTERS = list(FEATURE_ROUTING.keys())

# H (forecast lead) per cell, in hours. Plan §0 / §2.
HORIZONS = {"day3": 72, "day7": 168}

# W (target window width), in hours. Plan §2: start at 24h, widen only if a
# cell's positive count is too sparse to clear the feasibility gate.
DEFAULT_WINDOW_HOURS = 24

# Plan §4: positive-count gate deciding whether a cell gets the full ML
# pipeline, a high-variance-but-trained model, or falls back to a physical rule.
FEASIBILITY_LOW = 150
FEASIBILITY_HIGH = 500

# Plan §5 starting hyperparameters for rare-event tabular classification.
XGB_PARAMS = dict(
    objective="binary:logistic",
    eval_metric="aucpr",
    max_depth=4,
    min_child_weight=5,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=2.0,
    reg_alpha=0.5,
    learning_rate=0.03,
    n_estimators=2000,
    tree_method="hist",
    early_stopping_rounds=100,
)

# Plan §6 baseline #2: single-feature physical threshold per disaster, and
# which direction counts as "alert" (flood/rain/wind/landslide alert on high
# values; cyclone alerts on low pressure).
BASELINE_FEATURES = {
    "y_lu_lut": ("precip_7d_sum", "high"),
    "y_sat_lo": ("landslide_trigger_index", "high"),
    "y_dong_loc": ("pressure_min_24h", "low"),
    "y_mua_lon": ("precip_3d_sum", "high"),
    "y_mua_da": ("wind_gust_max_24h", "high"),
}

# inference_plan.md §3: a cell only serves its ML probability when it clears
# both bars on its own headline test fold -- beats the single-feature
# baseline on PR-AUC, and isn't actively anti-predictive on ROC-AUC. Cells
# that fail this (e.g. day7 until Previous Runs is wired in) auto-fall-back
# to the rule at serve time; baked into the artifact at train time so
# inference.py never has to recompute it.
ROC_AUC_FLOOR = 0.55


def compute_serve_enabled(model_pr_auc: float, baseline_pr_auc: float, model_roc_auc: float) -> bool:
    return bool(model_pr_auc > baseline_pr_auc and model_roc_auc >= ROC_AUC_FLOOR)


def load_features(path: Path = DEFAULT_FEATURES_PATH) -> pd.DataFrame:
    """Load the engineered feature/label table, deduplicated and sorted.

    Some raw pulls contain exact-duplicate (location_id, time) rows (a known
    data issue, not a modeling choice) -- these break every row-position-based
    operation downstream (rolling windows, the label shift below), which all
    assume exactly one row per location per hour, so duplicates are dropped
    here rather than left for each caller to rediscover independently.
    """
    df = pd.read_csv(path)
    df["time"] = pd.to_datetime(df["time"])
    df = df.drop_duplicates(subset=["location_id", "time"])
    return df.sort_values(["location_id", "time"]).reset_index(drop=True)


def _forward_window_any(raw: pd.Series, horizon_hours: int, window_hours: int) -> np.ndarray:
    """For a single location's hourly 0/1 series, return, per row `i`, whether
    the event occurs in `[i + horizon_hours, i + horizon_hours + window_hours)`
    -- NaN where that window runs past the end of the available series.
    """
    shifted = raw.shift(-horizon_hours)
    reversed_max = shifted[::-1].rolling(window=window_hours, min_periods=window_hours).max()
    return reversed_max[::-1].to_numpy()


def add_windowed_labels(
    df: pd.DataFrame,
    horizon_hours: int,
    window_hours: int = DEFAULT_WINDOW_HOURS,
    label_cols: list[str] = TRAINING_LABEL_COLUMNS,
) -> pd.DataFrame:
    """Replace each raw point-in-time label column with the any-occurrence-in-
    window target the plan trains on (§2): 1 if the disaster occurs anywhere in
    `[issue_time + horizon_hours, issue_time + horizon_hours + window_hours)`.

    Rows near the end of each location's series (window runs past available
    data) get NaN and must be dropped before training -- the outcome there is
    genuinely unknown, not a legitimate negative.
    """
    df = df.copy()
    for col in label_cols:
        df[col] = df.groupby("location_id")[col].transform(
            lambda s: _forward_window_any(s, horizon_hours, window_hours)
        )
    return df


def feasibility_gate(y: pd.Series, low: int = FEASIBILITY_LOW, high: int = FEASIBILITY_HIGH) -> str:
    """Classify a cell's positive count per plan §4:
    "insufficient" (< low: use a physical-threshold rule instead of ML),
    "high_variance" (train, but expect variance; sigmoid calibration only), or
    "ok" (full pipeline).
    """
    n_pos = int(y.sum())
    if n_pos < low:
        return "insufficient"
    if n_pos < high:
        return "high_variance"
    return "ok"


def make_walk_forward_folds(
    issue_times: pd.Series,
    n_folds: int = 3,
    test_size: str = "60D",
    cal_size: str = "30D",
    embargo: str = "10D",
) -> list[dict[str, tuple[pd.Timestamp, pd.Timestamp]]]:
    """Build walk-forward (expanding-window) train/cal/test time boundaries
    (plan §3): train always starts at the earliest available issue_time and
    expands; cal and test are fixed-size blocks that step backward in time for
    each older fold, each separated by an embargo so no feature window on
    either side of a boundary overlaps the other split.

    Returns folds in chronological order -- the last entry is the "headline"
    fold (closest to production conditions).
    """
    times = pd.to_datetime(issue_times)
    t_min, t_max = times.min(), times.max()
    test_delta, cal_delta, embargo_delta = pd.Timedelta(test_size), pd.Timedelta(cal_size), pd.Timedelta(embargo)

    folds = []
    test_end = t_max
    for _ in range(n_folds):
        test_start = test_end - test_delta
        cal_end = test_start - embargo_delta
        cal_start = cal_end - cal_delta
        train_end = cal_start - embargo_delta
        if train_end <= t_min:
            break
        folds.append(
            {
                "train": (t_min, train_end),
                "cal": (cal_start, cal_end),
                "test": (test_start, test_end),
            }
        )
        test_end = test_start
    folds.reverse()
    return folds


def _block_mask(time: pd.Series, block: tuple[pd.Timestamp, pd.Timestamp]) -> pd.Series:
    start, end = block
    return (time > start) & (time <= end)


def pick_threshold(scores: np.ndarray, y_true: np.ndarray, beta: float = 2.0) -> float:
    """Pick the score threshold maximizing F-beta on (scores, y_true) -- meant
    to be called on the calibration block only (plan §5: threshold selection
    must come from cal, never from test)."""
    precision, recall, thresholds = precision_recall_curve(y_true, scores)
    precision, recall = precision[:-1], recall[:-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        f_beta = (1 + beta**2) * precision * recall / (beta**2 * precision + recall)
    f_beta = np.nan_to_num(f_beta)
    if len(f_beta) == 0:
        return 0.5
    return float(thresholds[np.argmax(f_beta)])


def score_metrics(scores: np.ndarray, y_true: np.ndarray, threshold: float, probabilistic: bool) -> dict:
    """PR-AUC (threshold-independent) plus F2/F3/precision/recall at a frozen
    threshold (plan §6); Brier score only makes sense for calibrated
    probabilities, not raw single-feature baseline scores."""
    y_true = np.asarray(y_true)
    predicted = (scores >= threshold).astype(int)
    tp = int(((predicted == 1) & (y_true == 1)).sum())
    fp = int(((predicted == 1) & (y_true == 0)).sum())
    fn = int(((predicted == 0) & (y_true == 1)).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    def f_beta(beta: float) -> float:
        denom = beta**2 * precision + recall
        return (1 + beta**2) * precision * recall / denom if denom else 0.0

    has_both_classes = len(np.unique(y_true)) > 1
    metrics = {
        "pr_auc": float(average_precision_score(y_true, scores)) if has_both_classes else float("nan"),
        "roc_auc": float(roc_auc_score(y_true, scores)) if has_both_classes else float("nan"),
        "precision": precision,
        "recall": recall,
        "f2": f_beta(2.0),
        "f3": f_beta(3.0),
        "n_pos": int(y_true.sum()),
        "n": len(y_true),
    }
    if probabilistic:
        metrics["brier"] = float(brier_score_loss(y_true, scores))
    return metrics


def climatological_baseline_metrics(
    df: pd.DataFrame, disaster: str, train_mask: pd.Series, cal_mask: pd.Series, test_mask: pd.Series
) -> dict:
    """Baseline #1 (plan §6): predict each row's historical by-month positive
    rate, estimated from the train block only. A single flat rate across the
    whole period would be a strawman for strongly seasonal, monsoon-driven
    hazards -- the model needs to beat actual seasonal climatology, not "no
    seasonality at all"."""
    train_month = df.loc[train_mask, "time"].dt.month
    ytr = df.loc[train_mask, disaster]
    overall_rate = float(ytr.mean()) if len(ytr) else 0.0
    month_rate = ytr.groupby(train_month).mean()

    def scores_for(mask: pd.Series) -> np.ndarray:
        months = df.loc[mask, "time"].dt.month
        return months.map(month_rate).fillna(overall_rate).to_numpy()

    cal_scores, cal_y = scores_for(cal_mask), df.loc[cal_mask, disaster].to_numpy()
    threshold = pick_threshold(cal_scores, cal_y, beta=2.0)

    test_scores, test_y = scores_for(test_mask), df.loc[test_mask, disaster].to_numpy()
    return score_metrics(test_scores, test_y, threshold, probabilistic=True)


def single_feature_baseline_metrics(
    df: pd.DataFrame, disaster: str, cal_mask: pd.Series, test_mask: pd.Series
) -> dict:
    """Baseline #2 (plan §6): the real bar. Alert when one routed feature
    crosses a threshold, chosen from the calibration block exactly like the
    model's threshold, then frozen and scored on test."""
    feature, direction = BASELINE_FEATURES[disaster]
    raw = df[feature].to_numpy()
    scores = raw if direction == "high" else -raw

    cal_scores, cal_y = scores[cal_mask.to_numpy()], df.loc[cal_mask, disaster].to_numpy()
    threshold = pick_threshold(cal_scores, cal_y, beta=2.0)

    test_scores, test_y = scores[test_mask.to_numpy()], df.loc[test_mask, disaster].to_numpy()
    metrics = score_metrics(test_scores, test_y, threshold, probabilistic=False)
    metrics["feature"] = feature
    metrics["direction"] = direction
    metrics["threshold"] = threshold
    return metrics


def _latest_positive_cal_mask(valid_df: pd.DataFrame, disaster: str, folds: list[dict]) -> pd.Series:
    """The most recent fold whose cal block alone contains a positive, for
    picking a baseline threshold when no fold clears the full train/cal/test
    bar. Vietnam's disasters are strongly seasonal, so a fixed-size cal block
    can land entirely in the off-season regardless of block size; falls back
    to all data up to the final test start (which does have positives,
    otherwise the cell wouldn't have reached this fallback path at all)."""
    for fold in reversed(folds):
        mask = _block_mask(valid_df["time"], fold["cal"])
        if valid_df.loc[mask, disaster].sum() > 0:
            return mask
    return valid_df["time"] <= folds[-1]["test"][0]


def _final_rule_artifact(valid_df: pd.DataFrame, disaster: str, folds: list[dict]) -> dict:
    """Baseline-rule descriptor persisted on EVERY cell's artifact, not just
    ones that fail the ML gate during training (inference_plan.md §2/§3):
    AUTO-mode serving needs a rule fallback ready for any cell whose gate
    fails live, even one that passed the gate at training time.

    `rule` stores plain data (feature/direction/threshold), not a callable --
    a callable would have to survive being pickled and unpickled by a
    separate serving process, which is fragile for no real benefit here.
    """
    feature, direction = BASELINE_FEATURES[disaster]
    if not folds or valid_df[disaster].sum() == 0:
        return {
            "rule": {"feature": feature, "direction": direction, "threshold": None},
            "rule_precision": 0.0,
            "base_rate": 0.0,
        }

    cal_mask = _latest_positive_cal_mask(valid_df, disaster, folds)
    threshold = single_feature_baseline_metrics(valid_df, disaster, cal_mask, cal_mask)["threshold"]

    test_mask = _block_mask(valid_df["time"], folds[-1]["test"])
    if valid_df.loc[test_mask, disaster].sum() > 0:
        precision = single_feature_baseline_metrics(valid_df, disaster, cal_mask, test_mask)["precision"]
    else:
        precision = 0.0

    base_rate = float(valid_df.loc[valid_df["time"] <= folds[-1]["cal"][1], disaster].mean())
    return {
        "rule": {"feature": feature, "direction": direction, "threshold": threshold},
        "rule_precision": precision,
        "base_rate": base_rate,
    }


def train_cell(
    df: pd.DataFrame,
    disaster: str,
    horizon_name: str,
    horizon_hours: int,
    window_hours: int = DEFAULT_WINDOW_HOURS,
    n_folds: int = 8,
    test_size: str = "60D",
    cal_size: str = "30D",
    embargo: str = "10D",
    params: dict | None = None,
) -> dict:
    """Run the reference walk-forward training loop (plan §8) for one
    (disaster, horizon) cell: label windowing, feasibility gate, per-fold
    train -> calibrate -> pick threshold -> evaluate, then a final refit for
    serving. `df` must already carry the windowed label for `disaster` at this
    horizon (see add_windowed_labels)."""
    params = dict(params or XGB_PARAMS)
    feature_cols = FEATURE_ROUTING[disaster]

    valid = df[disaster].notna()
    valid_df = df.loc[valid].reset_index(drop=True)
    tier = feasibility_gate(valid_df[disaster])

    folds = make_walk_forward_folds(valid_df["time"], n_folds, test_size, cal_size, embargo)
    fold_results = []
    headline_model = None
    headline_calibrator = None
    headline_threshold = None
    headline_fold = None
    headline_model_metrics = None
    headline_baseline_pr_auc = None

    for fold in folds:
        train_mask = _block_mask(valid_df["time"], fold["train"])
        cal_mask = _block_mask(valid_df["time"], fold["cal"])
        test_mask = _block_mask(valid_df["time"], fold["test"])

        ytr = valid_df.loc[train_mask, disaster].astype(int)
        yca = valid_df.loc[cal_mask, disaster].astype(int)
        yte = valid_df.loc[test_mask, disaster].astype(int)
        if ytr.sum() == 0 or yca.sum() == 0 or yte.sum() == 0:
            continue

        baseline_clim = climatological_baseline_metrics(valid_df, disaster, train_mask, cal_mask, test_mask)
        baseline_single = single_feature_baseline_metrics(valid_df, disaster, cal_mask, test_mask)

        model_metrics = None
        if tier != "insufficient":
            Xtr, Xca, Xte = (valid_df.loc[m, feature_cols] for m in (train_mask, cal_mask, test_mask))
            scale_pos_weight = (ytr == 0).sum() / max((ytr == 1).sum(), 1)
            model = XGBClassifier(**params, scale_pos_weight=scale_pos_weight)
            model.fit(Xtr, ytr, eval_set=[(Xca, yca)], verbose=False)

            calibrator = CalibratedClassifierCV(model, method="sigmoid", cv="prefit")
            calibrator.fit(Xca, yca)

            cal_probs = calibrator.predict_proba(Xca)[:, 1]
            threshold = pick_threshold(cal_probs, yca.to_numpy(), beta=2.0)

            test_probs = calibrator.predict_proba(Xte)[:, 1]
            model_metrics = score_metrics(test_probs, yte.to_numpy(), threshold, probabilistic=True)

            headline_model, headline_calibrator, headline_threshold = model, calibrator, threshold
            headline_fold = fold
            headline_model_metrics = model_metrics
            headline_baseline_pr_auc = baseline_single["pr_auc"]

        fold_results.append(
            {
                "fold_test_start": fold["test"][0],
                "model": model_metrics,
                "baseline_climatological": baseline_clim,
                "baseline_single_feature": baseline_single,
            }
        )

    summary = {
        "disaster": disaster,
        "horizon": horizon_name,
        "horizon_hours": horizon_hours,
        "window_hours": window_hours,
        "tier": tier,
        "n_pos_total": int(valid_df[disaster].sum()),
        "n_total": int(len(valid_df)),
        "n_folds_run": len(fold_results),
        "fold_results": fold_results,
        "headline": fold_results[-1] if fold_results else None,
    }

    # inference_plan.md §2/§3: every cell ships a rule fallback alongside
    # whatever ML it has (or doesn't) -- AUTO mode needs it regardless of kind.
    rule_artifact = _final_rule_artifact(valid_df, disaster, folds)
    fold_params = {"n_folds": n_folds, "test_size": test_size, "cal_size": cal_size, "embargo": embargo}

    if headline_model is not None and folds:
        # Plan §8: final production model refits on all data up to the frozen
        # holdout, keeping the last fold's threshold and calibrator (no fresh
        # cal block remains once that data is folded into training).
        final_train_mask = valid_df["time"] <= folds[-1]["cal"][1]
        Xall = valid_df.loc[final_train_mask, feature_cols]
        yall = valid_df.loc[final_train_mask, disaster].astype(int)
        final_params = dict(params)
        # best_iteration is 0-indexed (the round the eval metric peaked at, per
        # early stopping on the cal block); +1 gives the matching tree count.
        final_params["n_estimators"] = int(headline_model.best_iteration) + 1
        final_params.pop("early_stopping_rounds", None)
        final_model = XGBClassifier(**final_params, scale_pos_weight=(yall == 0).sum() / max((yall == 1).sum(), 1))
        final_model.fit(Xall, yall, verbose=False)

        serve_enabled = compute_serve_enabled(
            headline_model_metrics["pr_auc"], headline_baseline_pr_auc, headline_model_metrics["roc_auc"]
        )

        summary["artifact"] = {
            "kind": "model",
            "model": final_model,
            "calibrator": headline_calibrator,
            "threshold": headline_threshold,
            "features": feature_cols,
            "serve_enabled": serve_enabled,
            "disaster": disaster,
            "horizon": horizon_name,
            "horizon_hours": horizon_hours,
            "window_hours": window_hours,
            "tier": tier,
            **rule_artifact,
            # The exact fold whose threshold/calibrator were frozen above --
            # evaluation.py re-scores this same held-out block rather than
            # re-deriving fold boundaries independently.
            "headline_test_block": headline_fold["test"],
            "fold_params": fold_params,
        }
    else:
        # Feasibility gate failed (or no fold cleared it): ship the baseline
        # physical-threshold rule instead of a model (plan §4/§7).
        summary["artifact"] = {
            "kind": "baseline",
            "model": None,
            "calibrator": None,
            "threshold": rule_artifact["rule"]["threshold"],
            "features": [rule_artifact["rule"]["feature"]],
            "serve_enabled": False,
            "disaster": disaster,
            "horizon": horizon_name,
            "horizon_hours": horizon_hours,
            "window_hours": window_hours,
            "tier": tier,
            **rule_artifact,
            # No fold cleared the full train/cal/test bar (that's why this cell
            # shipped a baseline rule), so there's no genuine dedicated holdout;
            # the most recent generated block is used for reporting only.
            "headline_test_block": folds[-1]["test"] if folds else None,
            "fold_params": fold_params,
        }

    return summary


def persist_artifact(summary: dict, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """Persist the {model, calibrator, threshold, features, rule, ...} bundle
    for one cell as a single .pkl (joblib's pickle-compatible format handles
    the XGBoost/sklearn objects directly; evaluation.py/inference.py load
    these same files)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{summary['disaster']}_{summary['horizon']}.pkl"
    joblib.dump(summary["artifact"], out_path)
    return out_path


def _aggregate_metric(fold_results: list[dict], block: str, metric: str) -> float:
    values = [fr[block][metric] for fr in fold_results if fr[block] is not None]
    return float(np.nanmean(values)) if values else float("nan")


def run_training_pipeline(
    features_path: Path = DEFAULT_FEATURES_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    window_hours: int = DEFAULT_WINDOW_HOURS,
    n_folds: int = 8,
    test_size: str = "60D",
    cal_size: str = "30D",
    embargo: str = "10D",
) -> pd.DataFrame:
    """Train and persist all 10 (5 disaster x 2 horizon) cells, matching the
    build order in plan §7: run every cell (feasibility gate decides ML vs.
    baseline per cell), report a summary row each."""
    df = load_features(features_path)

    rows = []
    for horizon_name, horizon_hours in HORIZONS.items():
        labeled = add_windowed_labels(df, horizon_hours, window_hours)
        for disaster in DISASTERS:
            summary = train_cell(
                labeled,
                disaster,
                horizon_name,
                horizon_hours,
                window_hours=window_hours,
                n_folds=n_folds,
                test_size=test_size,
                cal_size=cal_size,
                embargo=embargo,
            )
            persist_artifact(summary, output_dir)
            rows.append(
                {
                    "disaster": disaster,
                    "horizon": horizon_name,
                    "tier": summary["tier"],
                    "n_pos_total": summary["n_pos_total"],
                    "n_folds_run": summary["n_folds_run"],
                    "model_pr_auc": _aggregate_metric(summary["fold_results"], "model", "pr_auc"),
                    "model_roc_auc": _aggregate_metric(summary["fold_results"], "model", "roc_auc"),
                    "model_f2": _aggregate_metric(summary["fold_results"], "model", "f2"),
                    "baseline_single_feature_pr_auc": _aggregate_metric(
                        summary["fold_results"], "baseline_single_feature", "pr_auc"
                    ),
                    "baseline_climatological_pr_auc": _aggregate_metric(
                        summary["fold_results"], "baseline_climatological", "pr_auc"
                    ),
                    "kind": summary["artifact"]["kind"],
                    "serve_enabled": summary["artifact"]["serve_enabled"],
                }
            )

    summary_df = pd.DataFrame(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(output_dir / "training_summary.csv", index=False)
    return summary_df


if __name__ == "__main__":
    result = run_training_pipeline()
    print(result.to_string(index=False))
