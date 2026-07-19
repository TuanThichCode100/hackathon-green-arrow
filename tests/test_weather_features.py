import unittest

import numpy as np
import pandas as pd

from weather_data.build_weather_features import build_weather_features


class WeatherFeatureBuilderTest(unittest.TestCase):
    def setUp(self):
        self.data = pd.DataFrame(
            {
                "location_id": [0, 0, 0, 1, 1],
                "time": [
                    "2021-01-01T00:00",
                    "2021-01-01T01:00",
                    "2021-01-01T02:00",
                    "2021-01-01T00:00",
                    "2021-01-01T01:00",
                ],
                "temperature_2m (Â°C)": [20, 21, 22, 10, 11],
                "dew_point_2m (Â°C)": [18, 18, 19, 9, 9],
                "precipitation (mm)": [1, 2, 100, 4, 5],
                "rain (mm)": [1, 2, 100, 4, 5],
                "surface_pressure (hPa)": [1000, 999, 998, 900, 901],
                "wind_speed_10m (km/h)": [10, 20, 30, 5, 6],
                "wind_gusts_10m (km/h)": [20, 30, 40, 10, 12],
                "wind_direction_10m (°)": [0, 90, 180, 270, 0],
                "soil_moisture_0_to_7cm (m³/m³)": [0.2, 0.3, 0.4, 0.5, 0.6],
                "soil_moisture_7_to_28cm (m³/m³)": [0.4, 0.4, 0.5, 0.7, 0.8],
                "et0_fao_evapotranspiration (mm)": [0.1] * 5,
                "y_mua_lon": [0, 0, 1, 0, 1],
            }
        )

    def test_normalizes_names_and_preserves_labels(self):
        result = build_weather_features(self.data, show_progress=False)

        self.assertIn("temperature_2m", result)
        self.assertIn("y_mua_lon", result)
        self.assertNotIn("temperature_2m (Â°C)", result)
        self.assertEqual(result["y_mua_lon"].tolist(), [0, 0, 1, 0, 1])

    def test_rolling_features_are_causal_and_location_scoped(self):
        result = build_weather_features(self.data, show_progress=False)

        location_zero = result[result["location_id"].eq(0)].reset_index(drop=True)
        location_one = result[result["location_id"].eq(1)].reset_index(drop=True)
        self.assertTrue(np.isnan(location_zero.loc[0, "precipitation_sum_3h"]))
        self.assertEqual(location_zero.loc[1, "precipitation_sum_3h"], 1)
        self.assertEqual(location_zero.loc[2, "precipitation_sum_3h"], 3)
        self.assertTrue(np.isnan(location_one.loc[0, "precipitation_sum_3h"]))
        self.assertEqual(location_one.loc[1, "precipitation_sum_3h"], 4)

    def test_builds_wind_and_soil_features_when_inputs_exist(self):
        result = build_weather_features(self.data, show_progress=False)

        self.assertAlmostEqual(result.loc[0, "wind_direction_10m_cos"], 1.0)
        self.assertAlmostEqual(result.loc[1, "wind_direction_10m_sin"], 1.0)
        self.assertAlmostEqual(result.loc[0, "gust_factor"], 2.0)
        self.assertAlmostEqual(
            result.loc[0, "soil_moisture_mean_0_to_28cm"], 0.35
        )

    def test_aggregates_duplicate_location_timestamp_with_mean_and_label_or(self):
        duplicate_row = self.data.iloc[[0]].copy()
        duplicate_row["precipitation (mm)"] = 3
        duplicate_row["y_mua_lon"] = 1
        duplicate = pd.concat([self.data, duplicate_row], ignore_index=True)

        result = build_weather_features(duplicate, show_progress=False)
        first = result.loc[
            result["location_id"].eq(0)
            & result["time"].eq(pd.Timestamp("2021-01-01T00:00"))
        ].iloc[0]

        self.assertEqual(len(result), len(self.data))
        self.assertEqual(first["precipitation"], 2)
        self.assertEqual(first["y_mua_lon"], 1)

    def test_rejects_missing_hour_that_would_make_windows_inaccurate(self):
        irregular = self.data.drop(index=1)
        with self.assertRaisesRegex(ValueError, "gap-free hourly"):
            build_weather_features(irregular, show_progress=False)

    def test_rejects_non_numeric_weather_values(self):
        invalid = self.data.copy()
        invalid["precipitation (mm)"] = invalid["precipitation (mm)"].astype(
            "object"
        )
        invalid.loc[0, "precipitation (mm)"] = "invalid"
        with self.assertRaisesRegex(ValueError, "precipitation.*non-numeric"):
            build_weather_features(invalid, show_progress=False)

    def test_rejects_target_values_outside_binary_domain(self):
        invalid = self.data.copy()
        invalid.loc[0, "y_mua_lon"] = 2
        with self.assertRaisesRegex(ValueError, "must contain only 0/1"):
            build_weather_features(invalid, show_progress=False)


if __name__ == "__main__":
    unittest.main()
