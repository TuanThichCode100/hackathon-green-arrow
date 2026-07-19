# Feature Engineering & Data Processing Plan

## 1. Raw Feature Dictionary (Base Data)

Here is a breakdown of your raw dataset and how each variable functions within the physical environment.

### Identifiers & Time

- **location_id**: Spatial identifier. Used to group data for rolling calculations (do not calculate rolling rain across different cities).
- **time**: The hourly timestamp of the forecast/observation.

### Atmospheric (Volatility & Weather)

- **temperature_2m**: Air temperature at 2 meters above ground.
- **dew_point_2m**: The temperature at which air becomes saturated with water vapor.
- **surface_pressure**: Atmospheric pressure. Sudden drops indicate approaching storms/cyclones.
- **wind_speed_10m**: Sustained wind speed.
- **wind_gusts_10m**: Short, sudden bursts of high-speed wind. (Strong indicator for cyclones/hail).
- **cloud_cover**: Percentage of the sky covered by clouds.

### Hydrological & Soil (Accumulation & Saturation)

- **precipitation**: Total liquid equivalent of water falling from the sky (rain + snow).
- **rain**: Liquid precipitation only.
- **et0_fao_evapotranspiration**: The amount of water evaporating from the soil and transpiring from plants. (High values dry out the soil).
- **soil_temperature_0_to_7cm & soil_temperature_7_to_28cm**: Ground temperatures at surface and deep levels.
- **soil_moisture_0_to_7cm**: Surface soil wetness (reacts quickly to daily rain).
- **soil_moisture_7_to_28cm**: Deep soil wetness (reacts slowly, acts as a long-term reservoir; critical for landslides).

### Irrelevant Variables (To Be Dropped)

- **snow_depth & snowfall**: Vietnam is a tropical climate. Except for extremely rare micro-events in high mountains (e.g., Fansipan), these will be 0. They add zero variance and should be dropped to reduce noise.

## 2. Feature Engineering Pipeline (For 72h & 168h Horizons)

Because our goal is to predict macro-events 3 to 7 days into the future using Meteo API forecasts, we must transform the hourly API data into aggregated daily/multi-day windows.

### Step A: Time/Cyclical Encoding

Extreme weather is highly seasonal. The model needs to know if a heavy rain event is happening during monsoon season or the dry season.

**Extract**: Month and Day of Year.

**Transform**: Apply sine and cosine transformations so the model understands December (12) is next to January (1).

```
month_sin = sin(2 * pi * month / 12)
month_cos = cos(2 * pi * month / 12)
```

### Step B: Forecast Aggregations (The Core Features)

For a given target window (e.g., Day 7), aggregate the hourly forecasts leading up to and including that window.

#### Hydrological Accumulations (For Floods & Landslides)

- **precip_3d_sum**: Sum of precipitation over a 72-hour forecast window.
- **precip_7d_sum**: Sum of precipitation over a 168-hour forecast window.
- **evapo_3d_sum**: Sum of et0_fao_evapotranspiration. (Helps calculate net water retained).

#### Soil State Averages

- **deep_soil_moisture_3d_avg**: Mean of soil_moisture_7_to_28cm over 3 days. A consistently high average means the ground is saturated and cannot absorb more water.

#### Atmospheric Extremes (For Cyclones, Hail, Heavy Rain)

- **wind_gust_max_24h**: The absolute maximum wind_gusts_10m forecasted within the target day. (Hourly wind speed doesn't matter; the single strongest gust does).
- **pressure_min_24h**: The lowest forecasted surface_pressure during the target window.

#### Pressure Trends (Velocity of Change)

- **pressure_delta_48h**: The difference between the forecasted pressure on Day 3 vs Day 1. A severe negative delta is the primary physical signature of an approaching tropical depression/cyclone.

### Step C: Domain-Specific Feature Crosses

Combine variables to create powerful physical proxies.

#### Humidity Proxy
**temp_dew_spread = temperature_2m - dew_point_2m**

Logic: A spread close to 0 means 100% relative humidity. Crucial for heavy rain. Calculate the daily minimum spread.

#### Net Water Retention (NWR)
**NWR_7d = precip_7d_sum - evapo_7d_sum**

Logic: How much water actually stayed in the ground over a week, after the sun dried some of it up.

#### Landslide Trigger Index
**NWR_7d * deep_soil_moisture_3d_avg**

Logic: Landslides happen when high incoming water (NWR) hits already saturated ground (high deep soil moisture).

## 3. Feature Routing by Disaster Model

To prevent "noisy features" from confusing the XGBoost trees, strictly route these engineered features to the models that physically require them.

| Target | Routed Features |
|--------|-----------------|
| **y_lu_lut (Floods)** | precip_3d_sum, precip_7d_sum, NWR_7d, deep_soil_moisture_3d_avg, Seasonality (Sin/Cos) |
| **y_sat_lo (Landslides)** | Landslide Trigger Index, NWR_7d, deep_soil_moisture_3d_avg, Surface vs Deep Moisture Delta |
| **y_dong_loc (Cyclones)** | pressure_min_24h, pressure_delta_48h, wind_gust_max_24h, Seasonality |
| **y_mua_lon (Heavy Rain)** | temp_dew_spread, precip_3d_sum, cloud_cover_max, pressure_min_24h |
| **y_mua_da (Hail)** | temp_dew_spread, temperature_2m (min/max), wind_gust_max_24h, pressure_delta_48h. (Hail requires high atmospheric instability + temperature drops) |
