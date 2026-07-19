from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, PeftConfig

app = FastAPI(title="Green Arrow LLM Inference Server")

class PredictionRequest(BaseModel):
    commune: str
    prediction_data: dict
    audience: str # "can_bo" or "nguoi_dan"

# Global variables for model
tokenizer = None
model = None

def load_model():
    global tokenizer, model
    try:
        print("Loading Gemma base model and LoRA adapter...")
        # Lora path generated from Kaggle notebook
        peft_model_id = "gemma-4-E4B-it-weather-lora"
        config = PeftConfig.from_pretrained(peft_model_id)
        
        base_model = AutoModelForCausalLM.from_pretrained(
            config.base_model_name_or_path, 
            torch_dtype=torch.bfloat16, 
            device_map="auto"
        )
        model = PeftModel.from_pretrained(base_model, peft_model_id)
        tokenizer = AutoTokenizer.from_pretrained(peft_model_id)
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Failed to load model (this is expected if running without downloaded weights): {e}")

@app.on_event("startup")
async def startup_event():
    load_model()

@app.post("/generate_alert")
async def generate_alert(req: PredictionRequest):
    if req.audience not in ["can_bo", "nguoi_dan"]:
        raise HTTPException(status_code=400, detail="Audience must be 'can_bo' or 'nguoi_dan'")
        
    prompt = (
        f"Hãy đọc dữ liệu dự báo thời tiết sau cho khu vực {req.commune}, Điện Biên.\n"
        f"Dữ liệu JSON:\n{json.dumps(req.prediction_data, ensure_ascii=False, indent=2)}\n\n"
    )
    if req.audience == "can_bo":
        prompt += "Yêu cầu: Viết một thông báo dành cho cán bộ quản lý (CRM Chatbot). Hãy dùng giọng văn chuyên nghiệp, đúng chuyên môn, phân tích cụ thể các rủi ro, không dùng biểu tượng cảm xúc (icon) và trình bày rõ ràng để cán bộ dễ dàng đưa ra quyết định."
    else:
        prompt += "Yêu cầu: Viết một thông báo SMS/Zalo khẩn cấp dành cho người dân vùng cao. Cần trả lời cực kỳ ngắn gọn, súc tích, dễ hiểu đối với người không rành công nghệ, nêu bật ngay mức độ nguy hiểm để họ kịp thời phòng tránh."

    messages = [{"role": "user", "content": prompt}]
    
    if model is None or tokenizer is None:
        # Mock response if model not loaded
        return {
            "status": "mock", 
            "message": "Model not loaded. This is a mock response.",
            "generated_text": "CẢNH BÁO: Đây là tin nhắn giả lập vì model chưa được tải."
        }
        
    # Format according to Gemma's chat template
    inputs = tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(model.device)
    
    outputs = model.generate(inputs, max_new_tokens=256, temperature=0.7)
    # Decode only the generated part
    response_text = tokenizer.decode(outputs[0][inputs.shape[-1]:], skip_special_tokens=True)
    
    return {
        "status": "success",
        "generated_text": response_text
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6969)
