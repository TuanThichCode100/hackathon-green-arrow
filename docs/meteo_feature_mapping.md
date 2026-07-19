# Meteo ↔ Training Feature Mapping

Both `data/hourly_weather_meteo_data.csv` (raw Open-Meteo hourly pull) and the
training data (`data/df_sample.csv` / `data/weather_merged_2021_2026_labeled.csv`)
are normalized onto **one clean column-naming convention**, so meteo pulls can be
fed straight into the training pipeline. The training data originally embedded
units in column names (e.g. `"temperature_2m (°C)"`), which isn't a valid
identifier in several libraries (parentheses, `°`, `³`, `%`). Units are now
tracked separately instead — see `FEATURE_UNITS` below.

Implementation: [`src/pipelines/map_meteo_features.py`](../src/pipelines/map_meteo_features.py)

- `clean_training_schema()` — strips the `"(unit)"` suffix from the training
  data's columns. Output: `data/weather_merged_2021_2026_clean.csv`.
- `map_meteo_to_training_schema()` — maps a raw meteo pull onto the same clean
  schema. Output: `data/hourly_weather_meteo_data_mapped.csv`.
- `FEATURE_UNITS` — dict of clean feature name → unit, for reference/logging/plotting.
  Exported to `data/feature_units.csv`.

## Canonical clean schema

| Column | Unit |
|---|---|
| `location_id` | int |
| `time` | timestamp |
| `temperature_2m` | °C |
| `dew_point_2m` | °C |
| `precipitation` | mm |
| `surface_pressure` | hPa |
| `wind_speed_10m` | km/h |
| `cloud_cover` | % |
| `rain` | mm |
| `snow_depth` | m |
| `snowfall` | cm |
| `wind_gusts_10m` | km/h |
| `et0_fao_evapotranspiration` | mm |
| `soil_temperature_0_to_7cm` | °C |
| `soil_temperature_7_to_28cm` | °C |
| `soil_moisture_0_to_7cm` | m³/m³ |
| `soil_moisture_7_to_28cm` | m³/m³ |

(`y_mua_lon`, `y_sat_lo`, `y_dong_loc`, `y_mua_da`, `y_lu_lut` are labels, not
features — they pass through unchanged and aren't produced by the meteo mapping,
since they're what the model predicts.)

## Meteo → clean schema mapping

### Direct (same quantity, same unit — straight rename)

| Meteo column | → Clean column |
|---|---|
| `date` | `time` |
| `temperature_2m` | `temperature_2m` |
| `dew_point_2m` | `dew_point_2m` |
| `precipitation` | `precipitation` |
| `surface_pressure` | `surface_pressure` |
| `cloud_cover` | `cloud_cover` |
| `snow_depth` | `snow_depth` |
| `snowfall` | `snowfall` |
| `wind_gusts_10m` | `wind_gusts_10m` |

### Derived

| Clean column | Formula | Why |
|---|---|---|
| `rain` | `precipitation - showers` (clipped ≥ 0) | Open-Meteo defines `precipitation = rain + showers + snowfall (water equiv.)`. The meteo pull requested `precipitation` and `showers` but not `rain` directly, so it's backed out from those. |

### Approximated (flagged — not an exact match)

| Clean column | Approximated from | Caveat |
|---|---|---|
| `et0_fao_evapotranspiration` | `evapotranspiration` | These are two different Open-Meteo variables. `evapotranspiration` is the generic ET estimate; `et0_fao_evapotranspiration` is the FAO-56 Penman-Monteith reference ET. The meteo pull requested the former, not the latter. |
| `soil_temperature_0_to_7cm` | mean(`soil_temperature_0cm`, `soil_temperature_6cm`) | Meteo pull used point-depth soil variables (0/6/18cm) instead of the depth-band variables the training data uses. |
| `soil_temperature_7_to_28cm` | mean(`soil_temperature_6cm`, `soil_temperature_18cm`) | Same as above. |
| `soil_moisture_0_to_7cm` | mean(`soil_moisture_0_to_1cm`, `soil_moisture_1_to_3cm`, `soil_moisture_3_to_9cm`) | Same point-depth vs. depth-band mismatch. |
| `soil_moisture_7_to_28cm` | `soil_moisture_9_to_27cm` | Nearest available band to 7-28cm. |

### Missing (no substitute)

| Clean column | Status |
|---|---|
| `wind_speed_10m` | The meteo pull never requested this variable (only `wind_gusts_10m`, which is not a valid substitute for mean wind speed). Left as null. |

### Added at inference time, not present in the raw meteo file

| Clean column | Source |
|---|---|
| `location_id` | Not returned by a single-location Open-Meteo call — must be attached from `data/maping_location.csv` when looping over communes by lat/lon. |

## Recommended follow-up

Open-Meteo's hourly API directly exposes the exact variables the training
data uses — `wind_speed_10m`, `rain`, `et0_fao_evapotranspiration`,
`soil_temperature_0_to_7cm`, `soil_temperature_7_to_28cm`,
`soil_moisture_0_to_7cm`, `soil_moisture_7_to_28cm` — instead of the
point-depth soil variables and generic `evapotranspiration`/`precipitation`
currently requested in
[`notebook/get_meteo_data.ipynb`](../notebook/get_meteo_data.ipynb) and
[`src/pipelines/preprocess.py`](../src/pipelines/preprocess.py). Updating the
`hourly` params list in those two places to request the matching variable
names directly would remove every approximation above and fill in
`wind_speed_10m`, on the next data pull.
