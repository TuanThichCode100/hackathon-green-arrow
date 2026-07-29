# pyrefly: ignore [missing-import]
import nbformat as nbf
import os

nb = nbf.v4.new_notebook()
cells = []

# Title
cells.append(nbf.v4.new_markdown_cell(
"""# Hệ Thống Dự Báo Thời Tiết & Thiên Tai Điện Biên

Notebook này triển khai giải pháp dự báo thời tiết và cảnh báo thiên tai AI-Native (tham gia cuộc thi VAIC 2026), tập trung vào dữ liệu của tỉnh Điện Biên.

**Điểm nổi bật của kiến trúc:**
1. **Mô hình Dự báo PyTorch (Weather Forecaster):** Xử lý chuỗi thời gian (ConvLSTM-style) dự báo thời tiết và xác suất thiên tai.
2. **Hệ thống Dual-Role NLG (Gemma 4B LoRA):** Tạo cảnh báo bằng ngôn ngữ tự nhiên được cá nhân hóa theo 2 đối tượng:
   - **Cán bộ:** Cung cấp thông tin chi tiết (định dạng CRM), có số liệu hỗ trợ ra quyết định.
   - **Người dân:** Cảnh báo cực ngắn (Zalo, SMS), plain-text (không dấu cho SMS), ngôn ngữ cực kỳ đơn giản để dễ dàng phổ biến vùng cao.

---"""
))

cells.append(nbf.v4.new_markdown_cell("## 1. Cài đặt các thư viện cần thiết\nChúng ta cần cài đặt `cfgrib` để đọc GRIB file từ Copernicus, cùng với các công cụ lượng tử hóa 4-bit (`bitsandbytes`, `peft`) để fine-tune Gemma trên GPU T4."))
cells.append(nbf.v4.new_code_cell("!pip install -q cfgrib xarray eccodes peft bitsandbytes transformers scipy tqdm"))

cells.append(nbf.v4.new_markdown_cell("## 2. Import Thư Viện & Khai Báo Đường Dẫn Dữ Liệu\nKhai báo các thư viện PyTorch, Transformers, và Data Processing, đồng thời kiểm tra sự tồn tại của dữ liệu GRIB gốc và file ánh xạ 85 đơn vị hành chính cũ của Điện Biên."))
cells.append(nbf.v4.new_code_cell(
"""import os
import gc
import json
import numpy as np
import pandas as pd
import xarray as xr
import cfgrib
from scipy.spatial import cKDTree
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from tqdm.auto import tqdm

import warnings
warnings.filterwarnings('ignore')

# Đường dẫn tới dữ liệu Kaggle
GRIB_PATH = '/kaggle/input/datasets/phaichiuuuuuu/weather-vaic2026/66d11c9371efc5ab5ca44ddc280ad556.grib'
LOC_PATH = '/kaggle/input/datasets/phaichiuuuuuu/reference/dien_bien_locations.parquet'

print("Kiểm tra dữ liệu đầu vào:")
print(f"File GRIB tồn tại: {os.path.exists(GRIB_PATH)}")
print(f"File Locations tồn tại: {os.path.exists(LOC_PATH)}")"""
))

cells.append(nbf.v4.new_markdown_cell("## 3. Trích Xuất Dữ Liệu Lưới Theo 85 Vị Trí Hành Chính\nDữ liệu gốc (GRIB) lưu ở dạng lưới tọa độ. Bước này sử dụng thuật toán **Nearest-Neighbor (cKDTree)** để trích xuất nhanh chuỗi thời gian khí tượng tại chính xác 85 tọa độ xã/phường của Điện Biên, biến nó thành Tensor `(Thời gian, Số điểm, Số biến số)`."))
cells.append(nbf.v4.new_code_cell(
"""# Load GRIB with all hypercubes
print("Loading GRIB...")
import logging
logging.getLogger("cfgrib").setLevel(logging.ERROR) # Tắt warning dài dòng

datasets = cfgrib.open_datasets(GRIB_PATH, backend_kwargs={'indexpath': ''})

VARIABLES = [
    'u10', 'v10', 'd2m', 't2m', 'sp', 'tp',
    'fg10', 'tcc', 'sd', 'sf', 'stl1', 'swvl1',
    'swvl2', 'stl2', 'cp', 'e'
]

var_data_dict = {}
for ds in datasets:
    for var_name in VARIABLES:
        if var_name in ds.data_vars:
            if var_name not in var_data_dict:
                var_data_dict[var_name] = ds[var_name]

available_vars = list(var_data_dict.keys())
print(f"Available variables: {len(available_vars)}/{len(VARIABLES)}")

# Load Locations
locations = pd.read_parquet(LOC_PATH)
print(f"Loaded {len(locations)} old admin units.")
n_locs = len(locations)

# Trích xuất dựa trên cKDTree
first_var = var_data_dict[available_vars[0]]
grid_lats = first_var.latitude.values
grid_lons = first_var.longitude.values
grid_lon2d, grid_lat2d = np.meshgrid(grid_lons, grid_lats)
grid_points = np.column_stack([grid_lat2d.ravel(), grid_lon2d.ravel()])
tree = cKDTree(grid_points)

station_coords = locations[['latitude', 'longitude']].values
distances, indices = tree.query(station_coords)
print(f"Max distance to nearest grid point: {distances.max():.4f}°")

# Lấy dữ liệu cho từng vị trí và xử lý lệch time
timeseries_dict = {}
all_times = set()

print("Bắt đầu trích xuất dữ liệu không gian...")
for var_name in tqdm(available_vars, desc="Trích xuất không gian"):
    da = var_data_dict[var_name]
    
    t_coord = 'time' if 'time' in da.coords else 'valid_time' if 'valid_time' in da.coords else None
    
    dims = da.dims
    isel_dict = {}
    for d in dims:
        if d not in [t_coord, 'latitude', 'longitude']:
            isel_dict[d] = 0
    if isel_dict:
        da = da.isel(**isel_dict)
        
    var_data = da.values
    
    if t_coord is None or t_coord not in da.dims:
        var_data = var_data[np.newaxis, ...]
        times = np.array([np.datetime64('NaT')])
    else:
        times = da[t_coord].values
        if not np.issubdtype(times.dtype, np.datetime64):
            times = pd.to_datetime(times).values
        all_times.update(times)
        
    flat = var_data.reshape(var_data.shape[0], -1)
    extracted = flat[:, indices]
    
    timeseries_dict[var_name] = {'times': times, 'data': extracted}
    
    del var_data, flat
    gc.collect()

all_times = sorted([t for t in all_times if not pd.isna(t)])
common_times = np.array(all_times)
n_times = len(common_times)

# Gộp thành mảng 3 chiều: (T, N, C)
data_tensor = np.zeros((n_times, n_locs, len(available_vars)), dtype=np.float32)

print("Bắt đầu đồng bộ và nội suy thời gian...")
for vi, var_name in enumerate(tqdm(available_vars, desc="Nội suy thời gian")):
    ts_info = timeseries_dict[var_name]
    times = ts_info['times']
    data = ts_info['data']
    
    if pd.isna(times[0]):
        data_tensor[:, :, vi] = data[0]
    else:
        df = pd.DataFrame(data, index=times)
        df_reindexed = df.reindex(common_times).interpolate(method='nearest').ffill().bfill()
        data_tensor[:, :, vi] = df_reindexed.values

# Chuẩn hóa dữ liệu (Z-score normalization)
means = data_tensor.mean(axis=(0, 1), keepdims=True)
stds = data_tensor.std(axis=(0, 1), keepdims=True)
stds[stds < 1e-8] = 1.0  
data_normalized = (data_tensor - means) / stds

norm_stats = {
    'means': means.squeeze().tolist(),
    'stds': stds.squeeze().tolist(),
    'variables': available_vars,
    'location_ids': locations['location_id'].tolist(),
    'old_admin_units': locations['old_admin_unit'].tolist(),
}

timestamps = pd.to_datetime(common_times)
print("Hoàn tất trích xuất dữ liệu. Shape Tensor:", data_tensor.shape)"""
))

cells.append(nbf.v4.new_markdown_cell("## 4. Gán Nhãn Thiên Tai Dựa Trên Luật (Rule-Based Labeling)\nPhân tích dữ liệu lịch sử để tạo Ground Truth 5 loại thiên tai (Mưa lớn, Rét đậm, Gió lớn, Gió giật, Nguy cơ Lũ). \nLabel sẽ dùng để vừa train PyTorch model, vừa làm template tạo training set cho LLM."))
cells.append(nbf.v4.new_code_cell(
"""def label_disasters_from_raw(data_tensor, norm_stats, locations):
    var_idx = {name: i for i, name in enumerate(norm_stats['variables'])}
    T, N, C = data_tensor.shape
    labels = np.zeros((T, N, 7), dtype=np.float32)
    
    # 0: Mưa lớn (tp > 50mm/24h) theo Quyết định 18/2021/QĐ-TTg của Thủ tướng Chính phủ
    if 'tp' in var_idx:
        tp = data_tensor[:, :, var_idx['tp']]
        tp_mm = tp * 1000
        for loc in range(N):
            tp_series = pd.Series(tp_mm[:, loc])
            rain_24h = tp_series.rolling(24, min_periods=24).sum()
            labels[:, loc, 0] = (rain_24h > 50).values.astype(float)
    
    # 1: Rét đậm (nhiệt độ trung bình ngày < 15°C) theo khoản 6 Điều 3 Thông tư 25/2022/TT-BTNMT của Bộ Tài nguyên và Môi trường.
    if 't2m' in var_idx:
        t2m = data_tensor[:, :, var_idx['t2m']]
        t2m_celsius = t2m - 273.15
        for loc in range(N):
            daily_mean = pd.Series(t2m_celsius[:, loc]).rolling(24).mean()
            labels[:, loc, 1] = (daily_mean < 15).values.astype(float)
            
    # 2-5: Phân loại gió giật theo cấp
    if 'u10' in var_idx and 'v10' in var_idx:
        wind_speed = np.sqrt(data_tensor[:, :, var_idx['u10']]**2 + data_tensor[:, :, var_idx['v10']]**2)
        if 'fg10' in var_idx:
            gust_speed = data_tensor[:, :, var_idx['fg10']]
            max_wind = np.maximum(wind_speed, gust_speed)
        else:
            max_wind = wind_speed
            
        labels[:, :, 2] = ((max_wind >= 10.8) & (max_wind <= 17.1)).astype(float)
        labels[:, :, 3] = ((max_wind >= 17.2) & (max_wind <= 24.4)).astype(float)
        labels[:, :, 4] = ((max_wind >= 24.5) & (max_wind <= 32.6)).astype(float)
        labels[:, :, 5] = (max_wind >= 32.7).astype(float)
        
    # 6: Nguy cơ lũ (Mưa lớn cục bộ + Đất bão hòa > 0.35)
    if 'tp' in var_idx and 'swvl1' in var_idx:
        tp_mm = data_tensor[:, :, var_idx['tp']] * 1000
        swvl1 = data_tensor[:, :, var_idx['swvl1']]
        for loc in range(N):
            rain_6h = pd.Series(tp_mm[:, loc]).rolling(6, min_periods=6).sum()
            labels[:, loc, 6] = ((rain_6h > 30).values & (swvl1[:, loc] > 0.35)).astype(float)
            
    return labels

DISASTER_NAMES = ['heavy_rain', 'cold', 'wind_6_7', 'wind_8_9', 'wind_10_11', 'wind_12_17', 'flood_risk']
DISASTER_LABELS_VI = {
    'heavy_rain': 'Mưa lớn',
    'cold': 'Rét đậm rét hại',
    'wind_6_7': 'Gió giật cấp 6-7 (Cây cối rung chuyển, biển động)',
    'wind_8_9': 'Gió giật cấp 8-9 (Gãy cành cây, tốc mái nhà)',
    'wind_10_11': 'Gió giật cấp 10-11 (Đổ cây lớn, nhà cửa yếu)',
    'wind_12_17': 'Gió giật cấp 12-17 (Sức phá hoại cực kỳ lớn)',
    'flood_risk': 'Lũ quét / Sạt lở',
}

print("Tiến hành gán nhãn tự động...")
labels = label_disasters_from_raw(data_tensor, norm_stats, locations)
print("Hoàn tất. Labels shape:", labels.shape)"""
))

cells.append(nbf.v4.new_markdown_cell("## 5. Thiết Lập Hệ Thống Lời Nhắc (Prompts) Phân Quyền\nChúng ta định nghĩa 2 vai trò của LLM:\n- `ROLE_CANBO`: Cung cấp dữ liệu định lượng, chi tiết.\n- `ROLE_NGUOIDAN`: Cung cấp cảnh báo ngắn qua SMS/Zalo/Audio (bắt buộc loại bỏ dấu cho SMS và markdown)."))
cells.append(nbf.v4.new_code_cell(
"""import unicodedata

ROLE_CANBO_SYSTEM = \"\"\"Bạn là hệ thống CRM cảnh báo thiên tai tỉnh Điện Biên.
Vai trò: Hỗ trợ cán bộ PCTT truy vấn thông tin thời tiết và thiên tai real-time.
Quy tắc:
- Trả lời chi tiết, có số liệu cụ thể
- Nêu rõ mức cảnh báo (Xanh/Vàng/Cam/Đỏ)
- Đưa ra khuyến nghị hành động theo quy trình PCTT
- Trích dẫn nguồn dữ liệu và thời gian cập nhật
- Hỗ trợ so sánh, tổng hợp khi được yêu cầu\"\"\"

ROLE_NGUOIDAN_SYSTEM = \"\"\"Bạn là hệ thống cảnh báo thiên tai tỉnh Điện Biên.
Vai trò: Gửi thông báo khẩn cấp cho người dân.
Quy tắc BẮT BUỘC:
- Ngắn gọn nhất có thể. Tối đa 3 câu cho SMS, 6 câu cho Zalo.
- KHÔNG dùng markdown. Chỉ plain text.
- Nếu là định dạng SMS: KHÔNG dùng dấu tiếng Việt (vì SMS không hỗ trợ).
- Dùng từ đơn giản nhất. Người không biết chữ nghe đọc cũng hiểu.
- Luôn nói hành động cụ thể: lên cao, tránh suối, gọi 112.
- Luôn kèm số điện thoại khẩn cấp.
- Phù hợp để đọc qua loa phát thanh xã.\"\"\"

def remove_diacritics(text):
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))

def extract_readable_values(data_raw, t, loc, var_idx):
    vals = {}
    if 't2m' in var_idx:
        vals['temp'] = f"{data_raw[t, loc, var_idx['t2m']] - 273.15:.1f}°C"
    if 'tp' in var_idx:
        tp_series = pd.Series(data_raw[:, loc, var_idx['tp']] * 1000)
        vals['rain_24h'] = f"{tp_series.rolling(24, min_periods=1).sum().iloc[t]:.1f} mm"
        if t + 6 < len(data_raw):
            vals['rain_6h_forecast'] = f"{tp_series.iloc[t+1:t+7].sum():.1f} mm"
    if 'u10' in var_idx and 'v10' in var_idx:
        ws = np.sqrt(data_raw[t, loc, var_idx['u10']]**2 + data_raw[t, loc, var_idx['v10']]**2)
        vals['wind'] = f"{ws:.1f} m/s"
    if 'fg10' in var_idx:
        vals['gust'] = f"{data_raw[t, loc, var_idx['fg10']]:.1f} m/s"
    if 'swvl1' in var_idx:
        vals['soil'] = f"{data_raw[t, loc, var_idx['swvl1']]:.2f}"
    return vals

def compute_severity(labels_tensor, t, loc):
    # Cảnh báo ĐỎ nếu có: mưa lớn(0), gió cấp 10-11(4), gió cấp 12-17(5), hoặc lũ quét(6)
    if labels_tensor[t, loc, 0] > 0 or labels_tensor[t, loc, 4] > 0 or labels_tensor[t, loc, 5] > 0 or labels_tensor[t, loc, 6] > 0:
        return 'danger'
    if labels_tensor[t, loc].sum() > 0:
        return 'warning'
    return 'watch'

def generate_canbo_response(loc_old, loc_new, vals, disasters, severity, ts):
    severity_map = {'danger': 'ĐỎ - NGUY HIỂM', 'warning': 'CAM - CẢNH BÁO', 'watch': 'VÀNG - THEO DÕI'}
    lines = [
        f"TỔNG HỢP CẢNH BÁO - CẬP NHẬT {ts}",
        "",
        f"Khu vực: {loc_old} (nay thuộc {loc_new})",
        f"Mức cảnh báo: {severity_map.get(severity, 'VÀNG - THEO DÕI')}",
        "",
        "Số liệu:",
    ]
    if vals.get('rain_24h'): lines.append(f"- Lượng mưa 24h: {vals['rain_24h']}")
    if vals.get('temp'): lines.append(f"- Nhiệt độ: {vals['temp']}")
    if vals.get('wind'): lines.append(f"- Tốc độ gió: {vals['wind']}")
    if vals.get('soil'): lines.append(f"- Độ ẩm đất: {vals['soil']}")
    
    lines.extend(["", "Đánh giá rủi ro:"])
    for d in disasters:
        risk = "CAO" if severity == 'danger' else "TRUNG BÌNH"
        lines.append(f"- {DISASTER_LABELS_VI[d]}: {risk}")
    
    recs = [
        "1. Sơ tán hộ dân vùng nguy cơ cao ven suối, sườn dốc.",
        "2. Cử người canh gác các ngầm tràn."
    ] if severity == 'danger' else [
        "1. Thông báo thời tiết cho nhân dân."
    ]
    lines.extend(["", "Khuyến nghị:", *recs, "", "Nguồn: Hệ thống AI Dự Báo Điện Biên"])
    return "\\n".join(lines)

def generate_nguoidan_sms(loc_old, disasters, severity):
    loc_ascii = remove_diacritics(loc_old)
    action = "Len cho cao NGAY. Tranh suoi." if severity == 'danger' else "Theo doi thoi tiet."
    disaster_vi = {'heavy_rain': 'Mua to', 'cold': 'Ret dam', 'flood_risk': 'Nguy co lu'}
    hazard_text = ". ".join(disaster_vi.get(d, d) for d in disasters)
    
    sms = f"CANH BAO - {loc_ascii}\\n{hazard_text}.\\n{action}\\nGoi 112 neu can."
    return sms[:157] + "..." if len(sms) > 160 else sms

def generate_nguoidan_zalo(loc_old, disasters, severity, vals):
    loc_ascii = remove_diacritics(loc_old)
    disaster_vi = {'heavy_rain': 'mưa rất to', 'flood_risk': 'lũ quét và sạt lở'}
    hazard_list = " và ".join(disaster_vi.get(d, d) for d in disasters)
    
    lines = [
        f"CẢNH BÁO KHẨN CẤP - {loc_ascii}" if severity == 'danger' else f"CẢNH BÁO THỜI TIẾT - {loc_ascii}",
        "",
        f"Đang có {hazard_list}.",
        "",
        "Bạn cần làm ngay:" if severity == 'danger' else "Bạn nên:",
        "- Di chuyển lên cao, tránh xa suối" if severity == 'danger' else "- Theo dõi thời tiết",
        "Nếu gặp nguy hiểm, gọi ngay: 112"
    ]
    return "\\n".join(lines)"""
))

cells.append(nbf.v4.new_markdown_cell("## 6. Xây Dựng Tập Dữ Liệu Training Cho LLM\nChúng ta tạo ra các đoạn hội thoại mẫu (System, User, Model) bằng các hàm sinh ở trên. Dataset này dạy Gemma4 biết cách diễn giải số liệu thời tiết thành lời nói tự nhiên chuẩn xác."))
cells.append(nbf.v4.new_code_cell(
"""def build_training_pairs(data_raw, labels, norm_stats, locations, timestamps):
    var_idx = {name: i for i, name in enumerate(norm_stats['variables'])}
    pairs = []
    
    for t in tqdm(range(len(data_raw)), desc="Building pairs"):
        if t % 6 != 0: continue  # Lấy mẫu thưa để tiết kiệm RAM
            
        for loc in range(len(locations)):
            if labels[t, loc].sum() == 0: continue
            
            loc_info = locations.iloc[loc]
            loc_old, loc_new = loc_info['old_admin_unit'], loc_info['new_admin_unit']
            
            vals = extract_readable_values(data_raw, t, loc, var_idx)
            active_disasters = [DISASTER_NAMES[i] for i in range(len(DISASTER_NAMES)) if labels[t, loc, i] > 0]
            max_severity = compute_severity(labels, t, loc)
            
            
            structured_input = (
                f"Dia diem: {loc_old} (nay la {loc_new})\\nThoi gian: {timestamps[t]}\\n"
                f"Nhiet do: {vals.get('temp', 'N/A')}\\nLuong mua 24h: {vals.get('rain_24h', 'N/A')}\\n"
                f"Canh bao: {', '.join(active_disasters)}\\nMuc do: {max_severity}"
            )
            
            # 1. CÁN BỘ
            pairs.append({
                'system': ROLE_CANBO_SYSTEM,
                'input': f"Báo cáo tình hình {loc_old} hiện tại.",
                'output': generate_canbo_response(loc_old, loc_new, vals, active_disasters, max_severity, timestamps[t])
            })
            
            # 2. NGƯỜI DÂN - SMS
            pairs.append({
                'system': ROLE_NGUOIDAN_SYSTEM + "\\nFormat: SMS. Toi da 160 ky tu. Khong dau tieng Viet.",
                'input': structured_input,
                'output': generate_nguoidan_sms(loc_old, active_disasters, max_severity)
            })
            
            # 3. NGƯỜI DÂN - Zalo
            pairs.append({
                'system': ROLE_NGUOIDAN_SYSTEM + "\\nFormat: Zalo.",
                'input': structured_input,
                'output': generate_nguoidan_zalo(loc_old, active_disasters, max_severity, vals)
            })
            
    return pairs

print("Tạo dữ liệu huấn luyện...")
train_pairs = build_training_pairs(data_tensor, labels, norm_stats, locations, timestamps)
print(f"Đã tạo {len(train_pairs)} câu lệnh huấn luyện.")"""
))

cells.append(nbf.v4.new_markdown_cell("## 7. Khởi tạo LLM Gemma (LoRA + 4-bit)\nTải model `google/gemma-4-e4b-it` với định dạng 4-bit để vừa với VRAM 16GB của T4. Thiết lập tham số LoRA (r=16) để huấn luyện tiết kiệm."))
cells.append(nbf.v4.new_code_cell(
"""MODEL_ID = "google/gemma-4-e4b-it"

try:
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model_gemma = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
    )
    model_gemma = prepare_model_for_kbit_training(model_gemma)

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        lora_dropout=0.1,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model_gemma = get_peft_model(model_gemma, lora_config)
    print(f"Trainable params: {model_gemma.print_trainable_parameters()}")
    HAS_GEMMA = True
except Exception as e:
    print("Vui lòng đảm bảo bạn đã cung cấp HF_TOKEN (Secrets) và cấp quyền truy cập Gemma.")
    print(e)
    HAS_GEMMA = False"""
))

cells.append(nbf.v4.new_markdown_cell("## 8. Fine-Tuning Gemma Bằng PyTorch Native\nTriển khai vòng lặp huấn luyện thuần bằng PyTorch (không dùng thư viện HuggingFace Trainer) để đáp ứng yêu cầu năng lực kỹ thuật PyTorch của ban tổ chức. Tích hợp Gradient Accumulation & Clipping."))
cells.append(nbf.v4.new_code_cell(
"""class DualRoleAlertDataset(Dataset):
    def __init__(self, pairs, tokenizer, max_length=512):
        self.pairs = pairs
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self): return len(self.pairs)
    
    def __getitem__(self, idx):
        pair = self.pairs[idx]
        prompt = (f"<start_of_turn>system\\n{pair['system']}<end_of_turn>\\n"
                  f"<start_of_turn>user\\n{pair['input']}<end_of_turn>\\n"
                  f"<start_of_turn>model\\n{pair['output']}<end_of_turn>")
        
        encoded = self.tokenizer(prompt, truncation=True, max_length=self.max_length, padding='max_length', return_tensors='pt')
        input_ids = encoded['input_ids'].squeeze()
        mask = encoded['attention_mask'].squeeze()
        
        labels = input_ids.clone()
        model_start = prompt.find("<start_of_turn>model\\n")
        labels[:len(self.tokenizer.encode(prompt[:model_start + 21]))] = -100
        
        return {'input_ids': input_ids, 'attention_mask': mask, 'labels': labels}

if HAS_GEMMA and len(train_pairs) > 0:
    import random
    random.shuffle(train_pairs)
    train_ds = DualRoleAlertDataset(train_pairs[:int(len(train_pairs)*0.9)], tokenizer)
    
    train_loader = DataLoader(train_ds, batch_size=2, shuffle=True)
    optimizer = torch.optim.AdamW(filter(lambda p: p.requires_grad, model_gemma.parameters()), lr=2e-4)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    accumulation_steps = 4
    
    print("Đang huấn luyện LLM...")
    model_gemma.train()
    for step, batch in enumerate(tqdm(train_loader)):
        outputs = model_gemma(
            input_ids=batch['input_ids'].to(device),
            attention_mask=batch['attention_mask'].to(device),
            labels=batch['labels'].to(device)
        )
        loss = outputs.loss / accumulation_steps
        loss.backward()
        
        if (step + 1) % accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(model_gemma.parameters(), 1.0)
            optimizer.step()
            optimizer.zero_grad()
            
        if step > 100: break # Demo mode
            
    model_gemma.save_pretrained("best_dien_bien_alert_lora")
    tokenizer.save_pretrained("best_dien_bien_alert_lora")
    print("Huấn luyện thành công!")
    del model_gemma; gc.collect(); torch.cuda.empty_cache()"""
))

cells.append(nbf.v4.new_markdown_cell("## 9. Mô Hình Weather Forecaster (ConvLSTM-style)\nĐây là mô hình Học sâu thuần PyTorch, sử dụng Multi-task Learning để vừa dự đoán diễn biến thời tiết (Weather head) vừa chẩn đoán xác suất thiên tai (Disaster head) song song trên toàn bộ các xã."))
cells.append(nbf.v4.new_code_cell(
"""class EfficientLocationForecaster(nn.Module):
    def __init__(self, n_vars=16, n_locations=85, hidden_dim=128, n_layers=2, n_disasters=5):
        super().__init__()
        self.spatial_embed = nn.Sequential(
            nn.Linear(n_locations * n_vars, 256), nn.GELU(), nn.Linear(256, 128)
        )
        self.local_encoder = nn.Sequential(
            nn.Linear(n_vars, 64), nn.GELU(), nn.Linear(64, 64)
        )
        self.lstm = nn.LSTM(64 + 128, hidden_dim, num_layers=n_layers, batch_first=True)
        
        self.weather_head = nn.Sequential(nn.Linear(hidden_dim, 64), nn.GELU(), nn.Linear(64, n_vars))
        self.disaster_head = nn.Sequential(nn.Linear(hidden_dim, 64), nn.GELU(), nn.Linear(64, n_disasters))
    
    def forward(self, x):
        B, T, N, C = x.shape
        spatial_ctx = self.spatial_embed(x.reshape(B, T, N * C))
        combined = torch.cat([self.local_encoder(x), spatial_ctx.unsqueeze(2).expand(-1, -1, N, -1)], dim=-1)
        
        lstm_out, _ = self.lstm(combined.permute(0, 2, 1, 3).reshape(B * N, T, -1))
        last_hidden = lstm_out[:, -1, :]
        
        return self.weather_head(last_hidden).reshape(B, N, C), torch.sigmoid(self.disaster_head(last_hidden).reshape(B, N, -1))"""
))

cells.append(nbf.v4.new_markdown_cell("## 10. Huấn luyện Weather Forecaster (Hỗ Trợ Mixed Precision)\nBổ sung `torch.amp.autocast` và `GradScaler` để giảm một nửa yêu cầu bộ nhớ GPU (bfloat16) và huấn luyện cực nhanh."))
cells.append(nbf.v4.new_code_cell(
"""class DienBienWeatherDataset(Dataset):
    def __init__(self, data, labels, seq_len=24, horizon=6):
        self.data, self.labels = torch.FloatTensor(data), torch.FloatTensor(labels)
        self.seq_len, self.horizon = seq_len, horizon
    
    def __len__(self): return len(self.data) - self.seq_len - self.horizon
    
    def __getitem__(self, idx):
        return (self.data[idx : idx + self.seq_len], 
                self.data[idx + self.seq_len + self.horizon - 1],
                self.labels[idx + self.seq_len + self.horizon - 1])

# Chuẩn bị dữ liệu
T = len(data_normalized)
train_ds = DienBienWeatherDataset(data_normalized[:int(T*0.7)], labels[:int(T*0.7)])
train_loader = DataLoader(train_ds, batch_size=16, shuffle=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
weather_model = EfficientLocationForecaster(n_vars=len(available_vars), n_locations=len(locations)).to(device)
optimizer = torch.optim.AdamW(weather_model.parameters(), lr=1e-3)
scaler = torch.cuda.amp.GradScaler() if device == "cuda" else None

print("Huấn luyện Weather Forecaster...")
for epoch in range(3):
    weather_model.train()
    for seq, t_w, t_d in tqdm(train_loader, desc=f"Epoch {epoch+1}"):
        seq, t_w, t_d = seq.to(device), t_w.to(device), t_d.to(device)
        optimizer.zero_grad()
        
        if scaler:
            with torch.cuda.amp.autocast():
                p_w, p_d = weather_model(seq)
                loss = 0.7 * nn.MSELoss()(p_w, t_w) + 0.3 * nn.BCELoss()(p_d, t_d)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            p_w, p_d = weather_model(seq)
            loss = 0.7 * nn.MSELoss()(p_w, t_w) + 0.3 * nn.BCELoss()(p_d, t_d)
            loss.backward()
            optimizer.step()

torch.save(weather_model.state_dict(), "best_weather_model.pt")
print("Hoàn thành toàn bộ Pipeline Kaggle!")"""
))

nb.cells.extend(cells)

# Cấu hình Metadata kernel Python 3
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    },
    "language_info": {
        "codemirror_mode": {
            "name": "ipython",
            "version": 3
        },
        "file_extension": ".py",
        "mimetype": "text/x-python",
        "name": "python",
        "nbconvert_exporter": "python",
        "pygments_lexer": "ipython3",
        "version": "3.10.12"
    }
}

with open("kaggle_pipeline.ipynb", "w", encoding='utf-8') as f:
    nbf.write(nb, f)

print("Đã tạo kaggle_pipeline.ipynb với các Markdown giải thích chi tiết!")
