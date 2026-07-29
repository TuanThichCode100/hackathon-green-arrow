import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import joblib

from pipeline.evaluation.evaluate import evaluate_model
from pipeline.training.train import train_disaster_models
from tests.test_training import synthetic_training_data


class EvaluationPipelineTest(unittest.TestCase):
    def test_evaluator_cli_supports_cp1252_console_output(self):
        data = synthetic_training_data(120)
        bundle, _ = train_disaster_models(
            data,
            forecast_horizon_hours=3,
            max_iterations=1,
            require_calibration=False,
            show_progress=False,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model_path = root / "model.joblib"
            data_path = root / "holdout.csv"
            output_path = root / "evaluation.json"
            joblib.dump(bundle, model_path)
            data.iloc[60:].to_csv(data_path, index=False)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pipeline.evaluation.evaluate",
                    "--model",
                    str(model_path),
                    "--data",
                    str(data_path),
                    "--output",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONIOENCODING": "cp1252"},
            )

        self.assertIn("Macro PR-AUC:", result.stdout)

    def test_labeled_holdout_evaluation_reports_all_hazards_and_summary(self):
        data = synthetic_training_data(180)
        training_data = data.iloc[:120].copy()
        holdout_data = data.iloc[120:].copy()
        bundle, _ = train_disaster_models(
            training_data,
            forecast_horizon_hours=3,
            validation_fraction=0.2,
            calibration_fraction=0.2,
            max_iterations=5,
            require_calibration=False,
            show_progress=False,
        )

        report = evaluate_model(bundle, holdout_data)

        self.assertEqual(len(report["targets"]), 5)
        self.assertIn("macro_average_precision", report["summary"])
        self.assertIn(
            "invalid_average_precision_targets", report["summary"]
        )
        self.assertIn("brier_score", report["targets"]["y_mua_lon"])


if __name__ == "__main__":
    unittest.main()
