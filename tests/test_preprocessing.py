import unittest

import pandas as pd

from pipeline.shared.meteo_feature_mapping import (
    MODEL_FEATURE_COLUMNS,
    map_open_meteo_hourly_to_model_features,
)
from pipeline.preprocessing.open_meteo import preprocess_open_meteo_response


class MeteoFeatureMappingTest(unittest.TestCase):
    def test_api_response_preserves_both_hours_during_dst_fallback(self):
        times = [
            "2026-10-25T01:00",
            "2026-10-25T02:00",
            "2026-10-25T02:00",
            "2026-10-25T03:00",
        ]
        fields = [
            "temperature_2m",
            "dew_point_2m",
            "precipitation",
            "surface_pressure",
            "wind_speed_10m",
            "cloud_cover",
            "wind_gusts_10m",
            "et0_fao_evapotranspiration",
            "soil_temperature_0cm",
            "soil_temperature_6cm",
            "soil_temperature_18cm",
            "soil_moisture_0_to_1cm",
            "soil_moisture_1_to_3cm",
            "soil_moisture_3_to_9cm",
            "soil_moisture_9_to_27cm",
        ]
        payload = {
            "latitude": 52.52,
            "longitude": 13.41,
            "timezone": "Europe/Berlin",
            "hourly": {"time": times, **{field: [1.0] * 4 for field in fields}},
        }

        result = preprocess_open_meteo_response(payload)

        self.assertNotEqual(
            result.loc[1, "time"].utcoffset(), result.loc[2, "time"].utcoffset()
        )

    def test_open_meteo_hourly_data_is_mapped_to_training_contract(self):
        hourly = pd.DataFrame(
            {
                "temperature_2m": [25.0],
                "dew_point_2m": [20.0],
                "precipitation": [3.0],
                "surface_pressure": [950.0],
                "wind_speed_10m": [12.0],
                "cloud_cover": [80.0],
                "rain": [2.5],
                "snow_depth": [0.0],
                "snowfall": [0.0],
                "wind_gusts_10m": [25.0],
                "et0_fao_evapotranspiration": [0.2],
                "soil_temperature_0cm": [28.0],
                "soil_temperature_6cm": [25.0],
                "soil_temperature_18cm": [22.0],
                "soil_moisture_0_to_1cm": [0.10],
                "soil_moisture_1_to_3cm": [0.20],
                "soil_moisture_3_to_9cm": [0.40],
                "soil_moisture_9_to_27cm": [0.60],
            }
        )

        features = map_open_meteo_hourly_to_model_features(hourly)

        self.assertEqual(list(features.columns), MODEL_FEATURE_COLUMNS)
        self.assertAlmostEqual(features.loc[0, "soil_temperature_0_to_7cm (°C)"], 26.5)
        self.assertAlmostEqual(features.loc[0, "soil_temperature_7_to_28cm (°C)"], 22.0)
        self.assertAlmostEqual(
            features.loc[0, "soil_moisture_0_to_7cm (m³/m³)"],
            (0.10 * 1 + 0.20 * 2 + 0.40 * 4) / 7,
        )
        self.assertAlmostEqual(
            features.loc[0, "soil_moisture_7_to_28cm (m³/m³)"],
            (0.40 * 2 + 0.60 * 19) / 21,
        )

    def test_api_response_keeps_forecast_identity_and_model_features(self):
        variables = {
            "temperature_2m": [25.0],
            "dew_point_2m": [20.0],
            "precipitation": [3.0],
            "surface_pressure": [950.0],
            "wind_speed_10m": [12.0],
            "cloud_cover": [80.0],
            "rain": [2.5],
            "snow_depth": [0.0],
            "snowfall": [0.0],
            "wind_gusts_10m": [25.0],
            "et0_fao_evapotranspiration": [0.2],
            "soil_temperature_0cm": [28.0],
            "soil_temperature_6cm": [25.0],
            "soil_temperature_18cm": [22.0],
            "soil_moisture_0_to_1cm": [0.10],
            "soil_moisture_1_to_3cm": [0.20],
            "soil_moisture_3_to_9cm": [0.40],
            "soil_moisture_9_to_27cm": [0.60],
        }
        payload = {
            "latitude": 21.386,
            "longitude": 103.023,
            "timezone": "Asia/Bangkok",
            "hourly": {"time": ["2026-07-18T00:00"], **variables},
        }

        result = preprocess_open_meteo_response(payload)

        self.assertEqual(
            list(result.columns),
            ["time", "latitude", "longitude", *MODEL_FEATURE_COLUMNS],
        )
        self.assertEqual(
            result.loc[0, "time"].isoformat(), "2026-07-18T00:00:00+07:00"
        )
        self.assertEqual(result.loc[0, "latitude"], 21.386)


if __name__ == "__main__":
    unittest.main()
