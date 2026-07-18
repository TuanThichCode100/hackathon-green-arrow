import json
import os
import copy
import calendar

template_path = r"d:\Mini Project\hackathon-greenarrow-\notebooks\cds_tqdm_01_2001.ipynb"
with open(template_path, 'r', encoding='utf-8') as f:
    template_data = json.load(f)

years = [str(y) for y in range(2001, 2026, 2)]
months = [f"{m:02d}" for m in range(1, 13)]

batch_file_content = []
cleanup_file_content = []

for year in years:
    for month in months:
        notebook_data = copy.deepcopy(template_data)
        
        # Modify year and month
        source_cell_1 = notebook_data['cells'][1]['source']
        
        day_start_idx = -1
        day_end_idx = -1
        for i, line in enumerate(source_cell_1):
            if '"year": [' in line:
                source_cell_1[i] = f'    "year": ["{year}"],\n'
            elif '"month": [' in line:
                source_cell_1[i+1] = f'        "{month}"\n'
            elif '"day": [' in line:
                day_start_idx = i
            elif day_start_idx != -1 and day_end_idx == -1 and '],' in line:
                day_end_idx = i
        
        # Generate days list for this month and year
        num_days = calendar.monthrange(int(year), int(month))[1]
        days_str = [f'"{d:02d}"' for d in range(1, num_days + 1)]
        
        # Format days into groups of 3 for the notebook
        days_formatted = []
        for i in range(0, len(days_str), 3):
            group = ", ".join(days_str[i:i+3])
            if i + 3 < len(days_str):
                days_formatted.append(f'        {group},\n')
            else:
                days_formatted.append(f'        {group}\n')
                
        # Replace the days block
        if day_start_idx != -1 and day_end_idx != -1:
            source_cell_1 = source_cell_1[:day_start_idx+1] + days_formatted + source_cell_1[day_end_idx:]
            notebook_data['cells'][1]['source'] = source_cell_1
            
        # Modify output_filename in the third cell
        source_cell_2 = notebook_data['cells'][2]['source']
        for i, line in enumerate(source_cell_2):
            if 'output_filename =' in line:
                source_cell_2[i] = f'output_filename = "data/era5_data_{month}_{year}.zip"\n'
        
        filename = f"cds_tqdm_{month}_{year}.ipynb"
        filepath = os.path.join(r"d:\Mini Project\hackathon-greenarrow-\notebooks", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(notebook_data, f, indent=1)
        
        # Execute it in batch
        batch_file_content.append(f"start /B jupyter nbconvert --execute {filename}")
        
        # Add to cleanup if not the template
        if filename != "cds_tqdm_01_2001.ipynb":
            cleanup_file_content.append(f'del "{filename}"')

batch_filepath = os.path.join(r"d:\Mini Project\hackathon-greenarrow-\notebooks", "run_all.bat")
with open(batch_filepath, 'w', encoding='utf-8') as f:
    f.write("@echo off\n")
    f.write("echo Starting all notebooks...\n")
    f.write("\n".join(batch_file_content))
    f.write("\necho All notebook processes have been launched in the background.\n")
    f.write("pause\n")

cleanup_filepath = os.path.join(r"d:\Mini Project\hackathon-greenarrow-\notebooks", "cleanup.bat")
with open(cleanup_filepath, 'w', encoding='utf-8') as f:
    f.write("@echo off\n")
    f.write("echo Cleaning up generated notebooks (keeping the template cds_tqdm_01_2001.ipynb)...\n")
    f.write("\n".join(cleanup_file_content))
    f.write("\necho Cleanup complete!\n")
    f.write("pause\n")
    
print("Notebooks, run_all.bat, and cleanup.bat generated successfully.")
