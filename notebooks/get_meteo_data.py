import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

from pipeline.shared.meteo_feature_mapping import (
    map_open_meteo_hourly_to_model_features,
)

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 21.386,
	"longitude": 103.023,
	"daily": "weather_code",
	"hourly": ["temperature_2m", "dew_point_2m", "precipitation", "rain", "evapotranspiration", "wind_speed_10m", "wind_speed_80m", "wind_speed_120m", "wind_direction_10m", "wind_direction_80m", "wind_direction_120m", "wind_gusts_10m", "soil_temperature_0cm", "soil_temperature_6cm", "soil_temperature_18cm", "soil_moisture_0_to_1cm", "soil_moisture_1_to_3cm", "soil_moisture_3_to_9cm", "soil_moisture_9_to_27cm", "temperature_80m", "cloud_cover", "surface_pressure", "showers"],
	"timezone": "Asia/Bangkok",
	"start_date": "2026-04-18",
	"end_date": "2026-07-24",
}
responses = openmeteo.weather_api(url, params = params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
hourly_dew_point_2m = hourly.Variables(1).ValuesAsNumpy()
hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
hourly_rain = hourly.Variables(3).ValuesAsNumpy()
hourly_evapotranspiration = hourly.Variables(4).ValuesAsNumpy()
hourly_wind_speed_10m = hourly.Variables(5).ValuesAsNumpy()
hourly_wind_speed_80m = hourly.Variables(6).ValuesAsNumpy()
hourly_wind_speed_120m = hourly.Variables(7).ValuesAsNumpy()
hourly_wind_direction_10m = hourly.Variables(8).ValuesAsNumpy()
hourly_wind_direction_80m = hourly.Variables(9).ValuesAsNumpy()
hourly_wind_direction_120m = hourly.Variables(10).ValuesAsNumpy()
hourly_wind_gusts_10m = hourly.Variables(11).ValuesAsNumpy()
hourly_soil_temperature_0cm = hourly.Variables(12).ValuesAsNumpy()
hourly_soil_temperature_6cm = hourly.Variables(13).ValuesAsNumpy()
hourly_soil_temperature_18cm = hourly.Variables(14).ValuesAsNumpy()
hourly_soil_moisture_0_to_1cm = hourly.Variables(15).ValuesAsNumpy()
hourly_soil_moisture_1_to_3cm = hourly.Variables(16).ValuesAsNumpy()
hourly_soil_moisture_3_to_9cm = hourly.Variables(17).ValuesAsNumpy()
hourly_soil_moisture_9_to_27cm = hourly.Variables(18).ValuesAsNumpy()
hourly_temperature_80m = hourly.Variables(19).ValuesAsNumpy()
hourly_cloud_cover = hourly.Variables(20).ValuesAsNumpy()
hourly_surface_pressure = hourly.Variables(21).ValuesAsNumpy()
hourly_showers = hourly.Variables(22).ValuesAsNumpy()

hourly_data = {
	"date": pd.date_range(
		start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
		end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
		freq = pd.Timedelta(seconds = hourly.Interval()),
		inclusive = "left"
	).tz_convert(response.Timezone().decode())
}

hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["dew_point_2m"] = hourly_dew_point_2m
hourly_data["precipitation"] = hourly_precipitation
hourly_data["rain"] = hourly_rain
hourly_data["evapotranspiration"] = hourly_evapotranspiration
hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
hourly_data["wind_speed_80m"] = hourly_wind_speed_80m
hourly_data["wind_speed_120m"] = hourly_wind_speed_120m
hourly_data["wind_direction_10m"] = hourly_wind_direction_10m
hourly_data["wind_direction_80m"] = hourly_wind_direction_80m
hourly_data["wind_direction_120m"] = hourly_wind_direction_120m
hourly_data["wind_gusts_10m"] = hourly_wind_gusts_10m
hourly_data["soil_temperature_0cm"] = hourly_soil_temperature_0cm
hourly_data["soil_temperature_6cm"] = hourly_soil_temperature_6cm
hourly_data["soil_temperature_18cm"] = hourly_soil_temperature_18cm
hourly_data["soil_moisture_0_to_1cm"] = hourly_soil_moisture_0_to_1cm
hourly_data["soil_moisture_1_to_3cm"] = hourly_soil_moisture_1_to_3cm
hourly_data["soil_moisture_3_to_9cm"] = hourly_soil_moisture_3_to_9cm
hourly_data["soil_moisture_9_to_27cm"] = hourly_soil_moisture_9_to_27cm
hourly_data["temperature_80m"] = hourly_temperature_80m
hourly_data["cloud_cover"] = hourly_cloud_cover
hourly_data["surface_pressure"] = hourly_surface_pressure
hourly_data["showers"] = hourly_showers

hourly_dataframe = pd.DataFrame(data = hourly_data)
print("\nHourly data\n", hourly_dataframe)

# This is the exact feature contract consumed by the model. Keep the raw
# hourly_dataframe for diagnostics, but pass model_features to inference.
model_features = map_open_meteo_hourly_to_model_features(hourly_dataframe)
print("\nModel features\n", model_features)

# Process daily data. The order of variables needs to be the same as requested.
daily = response.Daily()
daily_weather_code = daily.Variables(0).ValuesAsNumpy()

daily_data = {
	"date": pd.date_range(
		start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
		end =  pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
		freq = pd.Timedelta(seconds = daily.Interval()),
		inclusive = "left"
	).tz_convert(response.Timezone().decode())
}

daily_data["weather_code"] = daily_weather_code

daily_dataframe = pd.DataFrame(data = daily_data)
print("\nDaily data\n", daily_dataframe)
