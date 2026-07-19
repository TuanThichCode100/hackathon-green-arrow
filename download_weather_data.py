"""
Download historical weather data from Open-Meteo API for all coordinates.
With retry logic and longer delays to handle rate limiting.
Resume support: skips already-downloaded files.
"""
import urllib.request
import urllib.error
import os
import time
import sys

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# All coordinates: URL (high precision) + Image (additional locations)
COORDINATES = [
    # From URL (coordinates 1-4, not in image)
    ("22.2642077", "102.3731569"),
    ("22.3757559", "102.2540299"),
    ("22.1574708", "102.5724901"),
    ("22.0619829", "102.5143555"),
    # From URL (coordinates 5-17, also in image with lower precision)
    ("21.9859511", "102.6031629"),
    ("21.833338", "102.7325616"),
    ("21.8272713", "103.1428346"),
    ("21.7258132", "102.7160411"),
    ("21.9896598", "102.9376092"),
    ("21.8098376", "102.9201731"),
    ("21.7586618", "103.0904718"),
    ("21.9519678", "103.0926433"),
    ("21.9312434", "103.2376065"),
    ("21.804404", "103.2258203"),
    ("21.5869655", "103.0296833"),
    ("21.9709478", "103.377406"),
    ("22.0538305", "103.3480596"),
    # From Image only (additional coordinates)
    ("21.94367", "103.3271"),
    ("22.03243", "103.4387"),
    ("21.84656", "103.4587"),
    ("21.64566", "103.3712"),
    ("21.54175", "103.4569"),
    ("21.72484", "103.3184"),
    ("21.72264", "103.4901"),
    ("21.61003", "103.3364"),
    ("21.5268", "103.2595"),
    ("21.56242", "103.1443"),
    ("21.54632", "103.2891"),
    ("21.45149", "103.3177"),
    ("21.44872", "103.135"),
    ("21.42151", "102.9734"),
    ("21.30182", "103.0465"),
    ("21.30607", "102.9473"),
    ("21.20723", "102.9487"),
    ("21.17925", "103.0526"),
    ("21.12695", "103.1005"),
    ("21.29673", "103.2201"),
    ("21.31829", "103.2996"),
    ("21.34569", "103.1345"),
    ("21.24692", "103.3802"),
    ("21.14146", "103.338"),
    ("21.12519", "103.2245"),
    ("22.03115", "103.1275"),
    ("21.49044", "103.1046"),
    ("21.38728", "103.0169"),
]

HOURLY_PARAMS = (
    "temperature_2m,relative_humidity_2m,dew_point_2m,wind_gusts_10m,"
    "wind_direction_10m,apparent_temperature,precipitation,rain,"
    "surface_pressure,cloud_cover,pressure_msl,wind_speed_10m,"
    "wind_speed_100m,wind_direction_100m,soil_temperature_0_to_7cm,"
    "soil_temperature_7_to_28cm,soil_moisture_0_to_7cm,"
    "soil_moisture_7_to_28cm,et0_fao_evapotranspiration,"
    "vapour_pressure_deficit,cloud_cover_high"
)

START_DATE = "2021-01-01"
END_DATE = "2026-06-30"
TIMEZONE = "Asia%2FBangkok"

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Rate limit settings
DELAY_BETWEEN_REQUESTS = 12  # seconds between requests
MAX_RETRIES = 5
INITIAL_BACKOFF = 30  # seconds for first retry after 429

total = len(COORDINATES)
success = 0
failed = 0
skipped = 0

print(f"Starting download of weather data for {total} coordinates...")
print(f"Output directory: {OUTPUT_DIR}")
print(f"Delay between requests: {DELAY_BETWEEN_REQUESTS}s")
print()

for i, (lat, lon) in enumerate(COORDINATES):
    idx = i + 1
    filename = f"weather_{lat}_{lon}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Resume support: skip if already downloaded
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        print(f"[{idx}/{total}] SKIP (already exists): {filename}")
        skipped += 1
        success += 1
        continue

    # Clean up any failed partial download
    if os.path.exists(filepath):
        os.remove(filepath)

    url = (
        f"{BASE_URL}?latitude={lat}&longitude={lon}"
        f"&start_date={START_DATE}&end_date={END_DATE}"
        f"&hourly={HOURLY_PARAMS}&timezone={TIMEZONE}&format=csv"
    )

    sys.stdout.write(f"[{idx}/{total}] Downloading: lat={lat}, lon={lon} ... ")
    sys.stdout.flush()

    downloaded = False
    for attempt in range(MAX_RETRIES):
        try:
            urllib.request.urlretrieve(url, filepath)
            file_size = os.path.getsize(filepath)
            file_size_mb = round(file_size / (1024 * 1024), 2)
            print(f"OK ({file_size_mb} MB)")
            success += 1
            downloaded = True
            break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                backoff = INITIAL_BACKOFF * (2 ** attempt)
                if attempt < MAX_RETRIES - 1:
                    sys.stdout.write(f"\n    Rate limited (429). Waiting {backoff}s before retry {attempt+2}/{MAX_RETRIES}... ")
                    sys.stdout.flush()
                    time.sleep(backoff)
                else:
                    print(f"FAILED after {MAX_RETRIES} retries: Rate limited (429)")
            else:
                print(f"FAILED: HTTP Error {e.code}")
                break
        except Exception as e:
            print(f"FAILED: {e}")
            break

    if not downloaded:
        failed += 1

    # Delay between requests to avoid rate limiting
    if i < total - 1:
        time.sleep(DELAY_BETWEEN_REQUESTS)

print()
print("=" * 50)
print("Download complete!")
print(f"  Total:   {total}")
print(f"  Success: {success}")
print(f"  Skipped: {skipped}")
print(f"  Failed:  {failed}")
print(f"  Output:  {OUTPUT_DIR}")
print("=" * 50)
