import json
import os
import time
import chromadb
from google import genai
from dotenv import load_dotenv

# โหลดตัวแปรจากไฟล์ .env
load_dotenv()

# 1. กำหนดตำแหน่งไฟล์และฐานข้อมูล
PROCESSED_DATA_PATH = "data/processed/subset_attack.json"
CHROMA_DB_PATH = "data/chroma_db"
COLLECTION_NAME = "mitre_attack_subset"

# 2. ตั้งค่า Client สำหรับ Gemini
api_key = os.getenv("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=api_key) if api_key else None

def get_embedding(text: str, client: genai.Client) -> list[float]:
    """ใช้ Gemini สร้าง Vector Embedding จากข้อความ (รุ่นใหม่ล่าสุด)"""
    response = client.models.embed_content(
        model='gemini-embedding-2',
        contents=text,
    )
    return response.embeddings[0].values

def ingest_to_chroma():
    if not gemini_client:
         raise ValueError("ไม่พบ GEMINI_API_KEY ในไฟล์ .env กรุณาตรวจสอบ")
    # อ่านข้อมูลที่กรองไว้แล้ว
    try:
        with open(PROCESSED_DATA_PATH, "r", encoding="utf-8") as f:
            techniques = json.load(f)
    except FileNotFoundError:
        print(f" Error: ไม่พบไฟล์ที่ {PROCESSED_DATA_PATH} กรุณารัน process_stix.py ก่อน")
        return

    # 3. ตั้งค่า ChromaDB
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    # ลบ Collection เดิมถ้ามี เพื่อเริ่มใหม่ (ป้องกันข้อมูลซ้ำซ้อน)
    try:
        chroma_client.delete_collection(name=COLLECTION_NAME)
    except:
        pass
        
    collection = chroma_client.create_collection(name=COLLECTION_NAME)

    docs = []
    metadatas = []
    ids = []
    embeddings = []

    print(f"กำลังแปลงข้อมูล {len(techniques)} เทคนิค ลงใน ChromaDB...")

    # 4. วนลูปสร้าง Embedding ทีละเทคนิค
    for t in techniques:
        # ประกอบข้อความให้มีบริบทชัดเจนขึ้นสำหรับทำ RAG
        doc_text = f"Technique: {t['technique_name']}\nTactic: {t['tactic']}\nDescription: {t['description']}"
        
        docs.append(doc_text)
        metadatas.append({
            "technique_id": t["technique_id"],
            "technique_name": t["technique_name"],
            "tactic": t["tactic"],
            "stix_version": "19.1"
        })
        ids.append(t["technique_id"])
        
        # แปลงข้อความเป็น Vector
        emb = get_embedding(doc_text, gemini_client)
        embeddings.append(emb)
        
        # หน่วงเวลา 3 วินาที ป้องกัน API โดนแบนชั่วคราว (Rate Limit)
        print(f"  -> Processed {t['technique_id']}... sleeping for 3 seconds")
        time.sleep(3)

    # 5. บันทึกลง ChromaDB
    collection.add(
        documents=docs,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

    print(f"สร้าง Vector Database สำเร็จ! บันทึกข้อมูลลงที่ {CHROMA_DB_PATH} เรียบร้อยแล้ว")

if __name__ == "__main__":
    ingest_to_chroma()