import json
import random
from datetime import datetime, timezone, timedelta

def create_mock_prediction():
    communes = ["Mường Chà", "Nậm Pồ", "Tủa Chùa", "Tuần Giáo", "Điện Biên Phủ", "Mường Nhé", "Mường Ảng", "Điện Biên Đông"]
    
    # We create a random prediction for a commune
    commune = random.choice(communes)
    forecast_time = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    
    return {
        "commune": commune,
        "prediction": {
            "forecast_time": forecast_time,
            "latitude": round(random.uniform(21.0, 22.0), 4),
            "longitude": round(random.uniform(102.0, 103.5), 4),
            "disasters": {
                "Mưa lớn": {"predicted": random.choice([True, False]), "probability_percent": round(random.uniform(0.01, 0.95), 4)},
                "Sạt lở": {"predicted": random.choice([True, False]), "probability_percent": round(random.uniform(0.01, 0.95), 4)},
                "Dông lốc": {"predicted": random.choice([True, False]), "probability_percent": round(random.uniform(0.01, 0.95), 4)},
                "Mưa đá": {"predicted": random.choice([True, False]), "probability_percent": round(random.uniform(0.01, 0.95), 4)},
                "Lũ lụt": {"predicted": random.choice([True, False]), "probability_percent": round(random.uniform(0.01, 0.95), 4)}
            }
        }
    }

def format_system_prompt(data, audience):
    prompt = (
        f"Hãy đọc dữ liệu dự báo thời tiết sau cho khu vực {data['commune']}, Điện Biên.\n"
        f"Dữ liệu JSON:\n{json.dumps(data['prediction'], ensure_ascii=False, indent=2)}\n\n"
    )
    if audience == "can_bo":
        prompt += "Yêu cầu: Viết một thông báo dành cho cán bộ quản lý (CRM Chatbot). Hãy dùng giọng văn chuyên nghiệp, đúng chuyên môn, phân tích cụ thể các rủi ro, không dùng biểu tượng cảm xúc (icon) và trình bày rõ ràng để cán bộ dễ dàng đưa ra quyết định."
    else:
        prompt += "Yêu cầu: Viết một thông báo SMS/Zalo khẩn cấp dành cho người dân vùng cao. Cần trả lời cực kỳ ngắn gọn, súc tích, dễ hiểu đối với người không rành công nghệ, nêu bật ngay mức độ nguy hiểm để họ kịp thời phòng tránh."
        
    return prompt

def generate_responses(data):
    # Determine the most critical disaster
    disasters = data["prediction"]["disasters"]
    critical = [k for k, v in disasters.items() if v["predicted"]]
    
    if not critical:
        cb_response = f"Báo cáo cập nhật thời tiết khu vực {data['commune']}: Dựa trên mô hình dự đoán lúc {data['prediction']['forecast_time']}, hiện tại không phát hiện rủi ro thiên tai đáng kể nào. Tỷ lệ xảy ra các hiện tượng cực đoan đều ở mức thấp. Đề nghị các đơn vị tiếp tục duy trì quan trắc."
        nd_response = f"THÔNG BÁO: Thời tiết khu vực {data['commune']} hiện tại bình thường, không có dấu hiệu thiên tai nguy hiểm. Bà con yên tâm sinh hoạt."
    else:
        critical_str = ", ".join(critical)
        cb_response = (
            f"BÁO CÁO KHẨN: Dự báo có nguy cơ cao xảy ra {critical_str} tại khu vực {data['commune']}. "
            f"Thời gian dự kiến: {data['prediction']['forecast_time']}. "
        )
        for d in critical:
            cb_response += f"Xác suất {d} là {disasters[d]['probability_percent']*100:.1f}%. "
        cb_response += "Đề nghị các cấp ủy, chính quyền địa phương lập tức triển khai phương án ứng phó, kiểm tra các khu vực xung yếu và sẵn sàng lực lượng cứu hộ."
        
        nd_response = (
            f"CẢNH BÁO KHẨN CẤP: Khu vực {data['commune']} sắp có {critical_str} nguy hiểm! "
            f"Bà con tuyệt đối không đi làm nương, tránh xa sông suối, sườn dốc ngay lập tức để bảo đảm an toàn tính mạng."
        )
        
    return cb_response, nd_response

def main():
    dataset = []
    
    # Generate 500 samples
    for _ in range(500):
        data = create_mock_prediction()
        cb_resp, nd_resp = generate_responses(data)
        
        # Format for 'Cán bộ'
        dataset.append({
            "messages": [
                {"role": "user", "content": format_system_prompt(data, "can_bo")},
                {"role": "model", "content": cb_resp}
            ]
        })
        
        # Format for 'Người dân'
        dataset.append({
            "messages": [
                {"role": "user", "content": format_system_prompt(data, "nguoi_dan")},
                {"role": "model", "content": nd_resp}
            ]
        })

    # Shuffle the dataset
    random.shuffle(dataset)
    
    output_path = "d:/Mini Project/New folder/hackathon-green-arrow/.agents/kaggle_dataset.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"Successfully generated {len(dataset)} training samples at {output_path}")

if __name__ == "__main__":
    main()
