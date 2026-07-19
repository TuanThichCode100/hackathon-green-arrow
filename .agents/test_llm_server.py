import requests
import json

def test_generate_alert(audience):
    url = "http://localhost:6969/generate_alert"
    
    # Mock data giống với dữ liệu dự đoán
    payload = {
        "commune": "Nậm Pồ",
        "prediction_data": {
            "forecast_time": "2026-07-20T12:00:00+07:00",
            "latitude": 21.9434,
            "longitude": 103.2392,
            "disasters": {
                "Mưa lớn": {"predicted": True, "probability_percent": 0.85},
                "Sạt lở": {"predicted": True, "probability_percent": 0.92},
                "Dông lốc": {"predicted": False, "probability_percent": 0.12},
                "Mưa đá": {"predicted": False, "probability_percent": 0.05},
                "Lũ lụt": {"predicted": True, "probability_percent": 0.76}
            }
        },
        "audience": audience
    }

    print(f"\n--- Gửi request test cho đối tượng: '{audience}' ---")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        print("Status:", result.get("status"))
        print("\n[VĂN BẢN TRẢ VỀ TỪ MODEL]:")
        print("="*50)
        print(result.get("generated_text"))
        print("="*50)
    except requests.exceptions.ConnectionError:
        print("Lỗi: Không thể kết nối tới server. Vui lòng đảm bảo bạn đã chạy 'python llm_server.py' (hoặc uvicorn) trên cổng 6969.")
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    print("Đang test LLM Server tại http://localhost:6969 ...")
    test_generate_alert("can_bo")
    test_generate_alert("nguoi_dan")
