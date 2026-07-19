import os
import glob
import pandas as pd
import re

def main():
    mapping_file = r"C:\Users\tranq\Downloads\maping_location.csv"
    weather_dir = r"d:\Mini Project\hackathon-green-arrow\weather_data"
    output_file = r"d:\Mini Project\hackathon-green-arrow\weather_merged_2021_2026_labeled.csv"
    
    print(f"Loading mapping from {mapping_file}...")
    df_map = pd.read_csv(mapping_file)
    
    location_mapping = {}
    for idx, row in df_map.iterrows():
        location_mapping[row['location_id']] = (float(row['latitude']), float(row['longitude']))

    print(f"Found {len(location_mapping)} locations in mapping file.")
    
    target_columns = [
        "location_id", "time", "temperature_2m (°C)", "dew_point_2m (°C)", "precipitation (mm)", 
        "surface_pressure (hPa)", "wind_speed_10m (km/h)", "cloud_cover (%)", "rain (mm)", 
        "snow_depth (m)", "snowfall (cm)", "wind_gusts_10m (km/h)", "et0_fao_evapotranspiration (mm)", 
        "soil_temperature_0_to_7cm (°C)", "soil_temperature_7_to_28cm (°C)", "soil_moisture_0_to_7cm (m³/m³)", 
        "soil_moisture_7_to_28cm (m³/m³)", "y_mua_lon", "y_sat_lo", "y_dong_loc", "y_mua_da", "y_lu_lut"
    ]
    
    csv_files = glob.glob(os.path.join(weather_dir, "*.csv"))
    print(f"Found {len(csv_files)} CSV files to merge.")
    
    all_data = []
    
    for f in csv_files:
        basename = os.path.basename(f)
        match = re.match(r"weather_([0-9\.]+)_([0-9\.]+)\.csv", basename)
        if not match:
            print(f"Warning: Could not parse {basename}")
            continue
            
        file_lat = float(match.group(1))
        file_lon = float(match.group(2))
        
        min_dist = float('inf')
        loc_id = -1
        for lid, (lat, lon) in location_mapping.items():
            dist = abs(file_lat - lat) + abs(file_lon - lon)
            if dist < min_dist:
                min_dist = dist
                loc_id = lid
                
        if min_dist > 0.0001:
             print(f"Warning: Closest location for {basename} is location_id {loc_id} with dist {min_dist}")
        
        try:
            df = pd.read_csv(f, skiprows=3)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            continue
            
        df['location_id'] = loc_id
        df['snow_depth (m)'] = 0.00
        df['snowfall (cm)'] = 0.00
        df['y_mua_lon'] = 0
        df['y_sat_lo'] = 0
        df['y_dong_loc'] = 0
        df['y_mua_da'] = 0
        df['y_lu_lut'] = 0
        
        df.columns = [c.strip() for c in df.columns]
        
        missing = []
        for col in target_columns:
            if col not in df.columns:
                missing.append(col)
        
        if missing:
            print(f"File {basename} is missing columns: {missing}")
            continue
            
        df_target = df[target_columns].copy()
        
        # Round the numerical defaults if needed, but they're just 0 and 0.0
        
        all_data.append(df_target)
        
    print(f"Successfully processed {len(all_data)} files.")
    
    if not all_data:
        print("No data to merge.")
        return
        
    print("Concatenating data...")
    merged_df = pd.concat(all_data, ignore_index=True)
    
    print("Sorting data by time, location_id...")
    merged_df.sort_values(by=["time", "location_id"], inplace=True)
    
    # Format floating point numbers to match sample closely (optional but good practice)
    # The sample has formatted floats but pandas to_csv default is fine
    
    print(f"Saving to {output_file}...")
    merged_df.to_csv(output_file, index=False)
    print("Done!")
    print(f"Total rows: {len(merged_df)}")
    print(f"Total columns: {len(merged_df.columns)}")
    unique_locs = merged_df['location_id'].nunique()
    print(f"Unique locations: {unique_locs}")

if __name__ == "__main__":
    main()
