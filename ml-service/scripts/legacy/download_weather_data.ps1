# Download historical weather data from Open-Meteo API for all coordinates
# Parameters match the user's selected features on the website

$outputDir = "d:\Mini Project\hackathon-green-arrow\weather_data"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# All coordinates: URL (high precision) + Image (additional locations)
$coordinates = @(
    # From URL (coordinates 1-4, not in image)
    @{ lat = "22.2642077"; lon = "102.3731569" },
    @{ lat = "22.3757559"; lon = "102.2540299" },
    @{ lat = "22.1574708"; lon = "102.5724901" },
    @{ lat = "22.0619829"; lon = "102.5143555" },
    # From URL (coordinates 5-17, also in image with lower precision)
    @{ lat = "21.9859511"; lon = "102.6031629" },
    @{ lat = "21.833338";  lon = "102.7325616" },
    @{ lat = "21.8272713"; lon = "103.1428346" },
    @{ lat = "21.7258132"; lon = "102.7160411" },
    @{ lat = "21.9896598"; lon = "102.9376092" },
    @{ lat = "21.8098376"; lon = "102.9201731" },
    @{ lat = "21.7586618"; lon = "103.0904718" },
    @{ lat = "21.9519678"; lon = "103.0926433" },
    @{ lat = "21.9312434"; lon = "103.2376065" },
    @{ lat = "21.804404";  lon = "103.2258203" },
    @{ lat = "21.5869655"; lon = "103.0296833" },
    @{ lat = "21.9709478"; lon = "103.377406" },
    @{ lat = "22.0538305"; lon = "103.3480596" },
    # From Image only (coordinates 14-41)
    @{ lat = "21.94367"; lon = "103.3271" },
    @{ lat = "22.03243"; lon = "103.4387" },
    @{ lat = "21.84656"; lon = "103.4587" },
    @{ lat = "21.64566"; lon = "103.3712" },
    @{ lat = "21.54175"; lon = "103.4569" },
    @{ lat = "21.72484"; lon = "103.3184" },
    @{ lat = "21.72264"; lon = "103.4901" },
    @{ lat = "21.61003"; lon = "103.3364" },
    @{ lat = "21.5268";  lon = "103.2595" },
    @{ lat = "21.56242"; lon = "103.1443" },
    @{ lat = "21.54632"; lon = "103.2891" },
    @{ lat = "21.45149"; lon = "103.3177" },
    @{ lat = "21.44872"; lon = "103.135" },
    @{ lat = "21.42151"; lon = "102.9734" },
    @{ lat = "21.30182"; lon = "103.0465" },
    @{ lat = "21.30607"; lon = "102.9473" },
    @{ lat = "21.20723"; lon = "102.9487" },
    @{ lat = "21.17925"; lon = "103.0526" },
    @{ lat = "21.12695"; lon = "103.1005" },
    @{ lat = "21.29673"; lon = "103.2201" },
    @{ lat = "21.31829"; lon = "103.2996" },
    @{ lat = "21.34569"; lon = "103.1345" },
    @{ lat = "21.24692"; lon = "103.3802" },
    @{ lat = "21.14146"; lon = "103.338" },
    @{ lat = "21.12519"; lon = "103.2245" },
    @{ lat = "22.03115"; lon = "103.1275" },
    @{ lat = "21.49044"; lon = "103.1046" },
    @{ lat = "21.38728"; lon = "103.0169" }
)

$hourlyParams = "temperature_2m,relative_humidity_2m,dew_point_2m,wind_gusts_10m,wind_direction_10m,apparent_temperature,precipitation,rain,surface_pressure,cloud_cover,pressure_msl,wind_speed_10m,wind_speed_100m,wind_direction_100m,soil_temperature_0_to_7cm,soil_temperature_7_to_28cm,soil_moisture_0_to_7cm,soil_moisture_7_to_28cm,et0_fao_evapotranspiration,vapour_pressure_deficit,cloud_cover_high"

$startDate = "2021-01-01"
$endDate = "2026-06-30"
$timezone = "Asia%2FBangkok"

$total = $coordinates.Count
$success = 0
$failed = 0

Write-Host "Starting download of weather data for $total coordinates..." -ForegroundColor Cyan
Write-Host "Output directory: $outputDir" -ForegroundColor Cyan
Write-Host ""

for ($i = 0; $i -lt $total; $i++) {
    $coord = $coordinates[$i]
    $lat = $coord.lat
    $lon = $coord.lon
    $idx = $i + 1
    
    $filename = "weather_${lat}_${lon}.csv"
    $filepath = Join-Path $outputDir $filename
    
    # Check if file already exists (resume support)
    if (Test-Path $filepath) {
        $fileSize = (Get-Item $filepath).Length
        if ($fileSize -gt 1000) {
            Write-Host "[$idx/$total] SKIP (already exists): $filename" -ForegroundColor Yellow
            $success++
            continue
        }
    }
    
    $url = "https://archive-api.open-meteo.com/v1/archive?latitude=${lat}&longitude=${lon}&start_date=${startDate}&end_date=${endDate}&hourly=${hourlyParams}&timezone=${timezone}&format=csv"
    
    Write-Host "[$idx/$total] Downloading: lat=$lat, lon=$lon ..." -NoNewline
    
    try {
        Invoke-WebRequest -Uri $url -OutFile $filepath -UseBasicParsing -ErrorAction Stop
        $fileSize = (Get-Item $filepath).Length
        $fileSizeMB = [math]::Round($fileSize / 1MB, 2)
        Write-Host " OK (${fileSizeMB} MB)" -ForegroundColor Green
        $success++
    }
    catch {
        Write-Host " FAILED: $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
    
    # Delay between requests to avoid rate limiting
    if ($i -lt ($total - 1)) {
        Start-Sleep -Milliseconds 1500
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Download complete!" -ForegroundColor Cyan
Write-Host "  Total: $total" -ForegroundColor White
Write-Host "  Success: $success" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor Red
Write-Host "  Output: $outputDir" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
