import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from pipeline.shared.meteo_feature_mapping import MODEL_FEATURE_COLUMNS
from pipeline.inference.predict import load_model
from pipeline.training.train import (
    TARGET_COLUMNS,
    _choose_threshold,
    _target_metrics,
    model_feature_columns,
    prepare_training_data,
    run_temporal_backtest,
    save_training_artifacts,
    train_disaster_models,
)


def synthetic_training_data(rows: int = 72) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rain = np.linspace(0, 30, rows)
    gust = np.linspace(5, 90, rows)
    soil = np.linspace(0.1, 0.65, rows)
    positions = np.arange(rows)
    values = {
        "location_id": np.arange(rows) % 3,
        "time": pd.date_range("2025-01-01", periods=rows, freq="h"),
        "temperature_2m": 20 + rng.normal(0, 3, rows),
        "dew_point_2m": 15 + rng.normal(0, 2, rows),
        "precipitation": rain,
        "surface_pressure": 950 + rng.normal(0, 5, rows),
        "wind_speed_10m": gust / 2,
        "cloud_cover": np.linspace(10, 100, rows),
        "rain": rain,
        "snow_depth": np.zeros(rows),
        "snowfall": np.zeros(rows),
        "wind_gusts_10m": gust,
        "et0_fao_evapotranspiration": rng.uniform(0, 0.5, rows),
        "soil_temperature_0_to_7cm": 22 + rng.normal(0, 2, rows),
        "soil_temperature_7_to_28cm": 21 + rng.normal(0, 2, rows),
        "soil_moisture_0_to_7cm": soil,
        "soil_moisture_7_to_28cm": soil * 0.9,
        "y_mua_lon": (positions % 5 == 0).astype(int),
        "y_sat_lo": (positions % 7 == 0).astype(int),
        "y_dong_loc": (positions % 9 == 0).astype(int),
        "y_mua_da": (positions % 11 == 0).astype(int),
        "y_lu_lut": (positions % 13 == 0).astype(int),
    }
    return pd.DataFrame(values)


class TrainingPipelineTest(unittest.TestCase):
    def test_threshold_search_can_select_probability_below_five_percent(self):
        labels = pd.Series([1, 1, 0, 0, 0, 0])
        probabilities = np.array([0.012, 0.010, 0.008, 0.006, 0.004, 0.002])

        threshold = _choose_threshold(
            labels, probabilities, max_alert_rate=0.5, min_recall=0.5
        )

        self.assertLess(threshold, 0.05)
        self.assertGreater(
            _target_metrics(labels, probabilities, threshold)["recall"], 0
        )

    def test_threshold_fallback_respects_hard_alert_budget(self):
        labels = pd.Series([1, 0, 0, 0])
        probabilities = np.array([0.9, 0.9, 0.1, 0.1])

        threshold = _choose_threshold(
            labels,
            probabilities,
            max_alert_rate=0.1,
            min_recall=0.9,
        )

        self.assertLessEqual(float(np.mean(probabilities >= threshold)), 0.1)

    def test_metrics_report_baseline_calibration_and_alert_rate(self):
        labels = pd.Series([1, 0, 0, 0])
        probabilities = np.array([0.8, 0.2, 0.1, 0.1])

        metrics = _target_metrics(labels, probabilities, threshold=0.5)

        self.assertIn("baseline_brier_score", metrics)
        self.assertIn("brier_skill_score", metrics)
        self.assertIn("expected_calibration_error", metrics)
        self.assertEqual(metrics["predicted_positive_rows"], 1)
        self.assertEqual(metrics["alert_rate"], 0.25)

    def test_temporal_backtest_reports_available_and_unavailable_folds(self):
        prepared = prepare_training_data(
            synthetic_training_data(180), forecast_horizon_hours=3
        )

        report = run_temporal_backtest(
            prepared,
            model_feature_columns(prepared),
            folds=2,
            max_iterations=1,
            random_state=42,
            show_progress=False,
        )

        self.assertEqual(len(report), 2)
        self.assertEqual(set(report[0]["targets"]), set(TARGET_COLUMNS))
        self.assertIn("available", report[0]["targets"]["y_mua_lon"])

    def test_training_rejects_target_without_positive_samples(self):
        data = synthetic_training_data()
        data["y_mua_lon"] = 0

        with self.assertRaisesRegex(ValueError, "y_mua_lon.*no positive"):
            train_disaster_models(
                data,
                max_iterations=1,
                require_calibration=False,
                show_progress=False,
            )

    def test_same_data_and_protocol_have_stable_experiment_key(self):
        data = synthetic_training_data()
        _, first = train_disaster_models(
            data,
            max_iterations=1,
            require_calibration=False,
            show_progress=False,
        )
        _, second = train_disaster_models(
            data,
            max_iterations=1,
            require_calibration=False,
            show_progress=False,
        )

        self.assertEqual(
            first["selection"]["experiment_key"],
            second["selection"]["experiment_key"],
        )

    def test_progress_output_has_separate_phases_and_complete_metrics(self):
        output = StringIO()

        with redirect_stdout(output):
            train_disaster_models(
                synthetic_training_data(120),
                forecast_horizon_hours=3,
                max_iterations=1,
                require_calibration=False,
                show_progress=True,
            )

        text = output.getvalue()
        self.assertIn("TRAIN:", text)
        self.assertIn("CALIBRATE:", text)
        self.assertIn("VALIDATE:", text)
        for field in [
            "PR-AUC=",
            "PR-lift=",
            "ROC-AUC=",
            "Brier=",
            "Brier-skill=",
            "ECE=",
            "precision=",
            "recall=",
            "F1=",
            "threshold=",
            "alert-rate=",
        ]:
            self.assertIn(field, text)

    def test_only_better_validation_run_is_promoted_as_best_model(self):
        data = synthetic_training_data()
        bundle, report = train_disaster_models(
            data,
            validation_fraction=0.25,
            max_iterations=5,
            require_calibration=False,
            show_progress=False,
        )
        report["selection"]["score"] = 0.70
        report["selection"]["eligible_for_promotion"] = True

        with tempfile.TemporaryDirectory() as directory:
            first = save_training_artifacts(bundle, report, directory)
            worse_report = {**report, "created_at": "2026-01-02T00:00:00+00:00"}
            worse_report["selection"] = {**report["selection"], "score": 0.60}
            second = save_training_artifacts(bundle, worse_report, directory)

            best_metrics = json.loads(
                (Path(directory) / "metrics.json").read_text(encoding="utf-8")
            )
            other_protocol_report = {
                **report,
                "created_at": "2026-01-03T00:00:00+00:00",
                "selection": {
                    **report["selection"],
                    "score": 0.10,
                    "experiment_key": "different-protocol",
                },
            }
            third = save_training_artifacts(
                bundle, other_protocol_report, directory
            )
            third_metrics = json.loads(
                third.run_metrics_path.read_text(encoding="utf-8")
            )
            restored_best = load_model(Path(directory) / "disaster_model.joblib")

        self.assertTrue(first.promoted_to_best)
        self.assertFalse(second.promoted_to_best)
        self.assertEqual(best_metrics["selection"]["score"], 0.70)
        self.assertNotEqual(first.run_directory, second.run_directory)
        self.assertTrue(third.promoted_to_best)
        self.assertIsNone(third_metrics["artifact"]["previous_best_score"])
        self.assertNotEqual(
            first.experiment_directory, third.experiment_directory
        )
        self.assertEqual(restored_best.created_at, bundle.created_at)

    def test_training_refuses_to_label_uncalibrated_scores_as_probabilities(self):
        with self.assertRaisesRegex(ValueError, "Cannot calibrate"):
            train_disaster_models(
                synthetic_training_data(),
                validation_fraction=0.25,
                max_iterations=5,
                show_progress=False,
            )

    def test_training_target_is_shifted_to_the_future_forecast_horizon(self):
        data = synthetic_training_data(6)
        data["location_id"] = 0
        data[TARGET_COLUMNS] = 0
        data.loc[4, "y_mua_lon"] = 1

        prepared = prepare_training_data(data, forecast_horizon_hours=2)

        row_at_two = prepared.loc[prepared["time"] == data.loc[2, "time"]].iloc[0]
        self.assertEqual(row_at_two["y_mua_lon"], 1)
        self.assertEqual(len(prepared), 4)

    def test_cli_artifact_can_be_loaded_by_inference_process(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "train.csv"
            output_dir = root / "artifacts"
            synthetic_training_data(30).to_csv(data_path, index=False)
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pipeline.training.train",
                    "--data",
                    str(data_path),
                    "--output-dir",
                    str(output_dir),
                    "--max-iterations",
                    "1",
                    "--forecast-horizon-hours",
                    "3",
                    "--allow-uncalibrated",
                ],
                check=True,
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONIOENCODING": "cp1252"},
            )
            run_model_path = next(
                (output_dir / "runs").glob("*/disaster_model.joblib")
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from pipeline.inference.predict import load_model; "
                        f"print(len(load_model(r'{run_model_path}').target_columns))"
                    ),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.stdout.strip(), "5")

    def test_training_accepts_unit_bearing_csv_headers(self):
        data = synthetic_training_data(4).rename(
            columns={"temperature_2m": "temperature_2m (°C)"}
        )

        prepared = prepare_training_data(data, forecast_horizon_hours=3)

        self.assertTrue(set(MODEL_FEATURE_COLUMNS).issubset(prepared.columns))

    def test_training_produces_reloadable_five_hazard_probability_model(self):
        data = synthetic_training_data()

        bundle, report = train_disaster_models(
            data,
            validation_fraction=0.25,
            max_iterations=20,
            random_state=7,
            require_calibration=False,
            show_progress=False,
        )

        probabilities = bundle.predict_proba(data.iloc[-3:][MODEL_FEATURE_COLUMNS])
        self.assertEqual(list(probabilities.columns), TARGET_COLUMNS)
        self.assertEqual(probabilities.shape, (3, 5))
        self.assertTrue(((probabilities >= 0) & (probabilities <= 1)).all().all())
        self.assertEqual(set(report["targets"]), set(TARGET_COLUMNS))

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.joblib"
            joblib.dump(bundle, path)
            restored = joblib.load(path)
            pd.testing.assert_frame_equal(
                probabilities,
                restored.predict_proba(data.iloc[-3:][MODEL_FEATURE_COLUMNS]),
            )

    def test_training_uses_derived_columns_from_feature_dataset(self):
        data = synthetic_training_data()
        data["precipitation_sum_24h"] = data["precipitation"].rolling(
            24, min_periods=1
        ).sum()

        bundle, report = train_disaster_models(
            data,
            validation_fraction=0.25,
            max_iterations=1,
            require_calibration=False,
            show_progress=False,
        )

        self.assertIn("precipitation_sum_24h", bundle.feature_columns)
        self.assertEqual(bundle.feature_columns, report["feature_columns"])
        self.assertNotIn("rain", bundle.feature_columns)
        self.assertIn("positive_counts_by_year", report["label_audit"])


if __name__ == "__main__":
    unittest.main()
