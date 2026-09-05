import os
import chromadb
from google import genai
from dotenv import load_dotenv

from src.schemas import ParsedAlert, TechniqueCandidate

load_dotenv()

CHROMA_DB_PATH = "data/chroma_db"
COLLECTION_NAME = "mitre_attack_subset"

# 1. ประกาศตัวแปร Client ไว้ด้านนอก (Singleton) เพื่อไม่ให้หน่วงระบบตอนเรียกใช้ซ้ำ
try:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    gemini_client = genai.Client(api_key=api_key) if api_key else None
    
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = chroma_client.get_collection(name=COLLECTION_NAME)
except Exception as e:
    collection = None
    print(f"Warning: ไม่สามารถเชื่อมต่อ ChromaDB ได้ (อย่าลืมรัน ingest_stix.py ก่อน): {e}")

def get_embedding(text: str) -> list[float]:
    """แปลงข้อความค้นหาเป็น Vector ด้วย Gemini"""
    response = gemini_client.models.embed_content(
        model='text-embedding-004',
        contents=text,
    )
    return response.embeddings[0].values

def retrieve_candidates(alert: ParsedAlert, predicted_tactics: list[str], top_k: int = 5) -> list[TechniqueCandidate]:
    """
    ดึง Candidate Techniques จาก Vector Database (ChromaDB)
    """
    if not collection or not gemini_client:
        print("Error: ฐานข้อมูล ChromaDB หรือ Gemini Client ยังไม่พร้อมทำงาน")
        return []

    # 1. สร้างคำค้นหา (Query) โดยเน้นไปที่สิ่งที่เกิดขึ้นใน Alert
    search_query = f"Observed Actions: {alert.observed_actions}. Context: {alert.narrative}"
    
    # 2. แปลงคำค้นหาเป็น เวกเตอร์
    query_embedding = get_embedding(search_query)

    # 3. สร้างเงื่อนไข (Filter) เพื่อกรองเฉพาะ Tactic ที่ Router ทายไว้
    where_clause = None
    if predicted_tactics:
        if len(predicted_tactics) == 1:
            where_clause = {"tactic": predicted_tactics[0]}
        else:
            # ใช้ $or กรณีที่มีหลาย Tactic (เช่น ["execution", "credential-access"])
            where_clause = {"$or": [{"tactic": t} for t in predicted_tactics]}

    # 4. ค้นหาใน ChromaDB โดยเอาเวกเตอร์มาเทียบความใกล้เคียง
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause
        )
    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        return []

    # 5. นำผลลัพธ์ที่ได้ แปลงกลับเข้า Pydantic Model (TechniqueCandidate)
    candidates = []
    if results and results.get('metadatas') and len(results['metadatas'][0]) > 0:
        for idx, metadata in enumerate(results['metadatas'][0]):
            
            # ดึงข้อความคำอธิบายจาก Document ตัดมาแสดงแค่ 250 ตัวอักษร
            full_doc = results['documents'][0][idx]
            desc_excerpt = full_doc[:250] + "..." if len(full_doc) > 250 else full_doc
            
            candidates.append(
                TechniqueCandidate(
                    technique_id=metadata["technique_id"],
                    technique_name=metadata["technique_name"],
                    tactic=metadata["tactic"],
                    description_excerpt=desc_excerpt,
                    stix_version=metadata["stix_version"]
                )
            )
            
    return candidates