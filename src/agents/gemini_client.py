import os
from google import genai
from google.genai import types

GEMINI_MODEL = "gemini-3.5-flash"

def _get_client() -> genai.Client:
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Set GOOGLE_API_KEY or GEMINI_API_KEY before calling Gemini")
    return genai.Client(api_key=key)

# 1. สร้าง Client เพียงครั้งเดียว (Singleton Pattern)
client = _get_client()

def generate_text(prompt: str, is_json: bool = False) -> str:
    """
    ฟังก์ชันเรียกใช้งาน Gemini API
    - is_json: เปิดเป็น True เพื่อบังคับให้โมเดลตอบกลับเป็น JSON Format 100%
    """
    
    # 2. ตั้งค่า Config: บังคับ Temperature = 0 เพื่อความนิ่งของคำตอบ
    config_args = {
        "temperature": 0.0, 
    }
    
    # 3. เปิดใช้งาน JSON Mode ตามต้องการ
    if is_json:
        config_args["response_mime_type"] = "application/json"
        
    config = types.GenerateContentConfig(**config_args)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=config
    )
    return response.text.strip()