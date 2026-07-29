import unittest

import pandas as pd

from pipeline.inference.predict import predict_hazards
from pipeline.shared.meteo_feature_mapping import MODEL_FEATURE_COLUMNS
from tests.test_training import synthetic_training_data
from pipeline.training.train import train_disaster_models


class InferencePipelineTest(unittest.TestCase):
    def test_inference_accepts_duplicate_dataframe_indices(self):
        training_data = synthetic_training_data()
        bundle, _ = train_disaster_models(
            training_data,
            validation_fraction=0.25,
            max_iterations=5,
            require_calibration=False,
            show_progress=False,
        )
        model_input = training_data.iloc[-2:][MODEL_FEATURE_COLUMNS].copy()
        model_input.insert(0, "longitude", 103.023)
        model_input.insert(0, "latitude", 21.386)
        model_input.insert(0, "time", training_data.iloc[-2:]["time"].values)
        model_input.index = [0, 0]

        result = predict_hazards(bundle, model_input)

        self.assertEqual(len(result), 2)

    def test_inference_returns_named_probabilities_and_decisions_per_hour(self):
        training_data = synthetic_training_data()
        bundle, _ = train_disaster_models(
            training_data,
            validation_fraction=0.25,
            max_iterations=10,
            require_calibration=False,
            show_progress=False,
        )
        model_input = training_data.iloc[-1:][MODEL_FEATURE_COLUMNS].copy()
        model_input.insert(0, "longitude", 103.023)
        model_input.insert(0, "latitude", 21.386)
        model_input.insert(0, "time", training_data.iloc[-1]["time"])

        result = predict_hazards(bundle, model_input)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["latitude"], 21.386)
        self.assertEqual(
            result[0]["forecast_time"],
            (training_data.iloc[-1]["time"] + pd.Timedelta(hours=24)).isoformat(),
        )
        self.assertEqual(len(result[0]["hazards"]), 5)
        self.assertEqual(result[0]["hazards"][0]["name"], "Mưa lớn")
        for hazard in result[0]["hazards"]:
            self.assertGreaterEqual(hazard["probability"], 0)
            self.assertLessEqual(hazard["probability"], 1)
            self.assertIsInstance(hazard["predicted"], bool)
            self.assertIsInstance(hazard["probability_calibrated"], bool)


if __name__ == "__main__":
    unittest.main()
