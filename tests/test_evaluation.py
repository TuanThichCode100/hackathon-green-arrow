import unittest

from pipeline.evaluation.evaluate import evaluate_model
from pipeline.training.train import train_disaster_models
from tests.test_training import synthetic_training_data


class EvaluationPipelineTest(unittest.TestCase):
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
