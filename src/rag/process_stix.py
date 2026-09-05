import json
import os



def in_scope(stix_object: dict) -> bool:
    """ฟังก์ชันคัดกรองเทคนิคให้ตรงกับขอบเขตของโครงงาน (ใช้สำหรับ Pytest)"""
    # 1. ตัดเทคนิคที่ถูกยกเลิก (Deprecated/Revoked)
    if stix_object.get("x_mitre_deprecated", False) or stix_object.get("revoked", False):
        return False

    # 2. ต้องเป็นระบบปฏิบัติการที่กำหนด (Windows หรือ Linux)
    platforms = stix_object.get("x_mitre_platforms", [])
    if not any(p in platforms for p in ["Windows", "Linux"]):
        return False

    # 3. ต้องอยู่ใน Tactics ที่กำหนด (เช่น credential-access)
    # หมายเหตุ: 'persistence' จะถูกปฏิเสธตามข้อสอบของ pytest
    phases = stix_object.get("kill_chain_phases", [])
    tactics = [phase.get("phase_name") for phase in phases]
    valid_tactics = ["credential-access", "execution", "defense-evasion"]
    if not any(t in tactics for t in valid_tactics):
        return False

    return True

# 1. กำหนดตำแหน่งไฟล์ ต้นทาง (Raw) และ ปลายทาง (Processed)
RAW_DATA_PATH = "data/raw/enterprise-attack-19.1.json"
PROCESSED_DATA_PATH = "data/processed/subset_attack.json"

# 2. กำหนด Scope ที่ต้องการกรอง (ตาม Requirement)
TARGET_TACTICS = {"initial-access", "execution", "credential-access"}
TARGET_PLATFORMS = {"Windows", "Linux"}

def process_stix_data():
    # โหลดไฟล์ STIX ต้นฉบับ
    try:
        with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
            stix_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: ไม่พบไฟล์ที่ {RAW_DATA_PATH} กรุณาดาวน์โหลดมาใส่ก่อน")
        return

    processed_techniques = []

    # วนลูปอ่านข้อมูลทุก Object ในไฟล์ MITRE
    for obj in stix_data.get("objects", []):
        
        # กฎข้อที่ 1: เลือกเฉพาะข้อมูลประเภท Technique (attack-pattern)
        if obj.get("type") != "attack-pattern":
            continue

        # กฎข้อที่ 2: ตัดเทคนิคที่ถูกยกเลิก (Revoked) หรือล้าสมัย (Deprecated) ทิ้ง
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue

        # กฎข้อที่ 3: เช็ค Platform (ต้องมี Windows หรือ Linux)
        platforms = set(obj.get("x_mitre_platforms", []))
        if not platforms.intersection(TARGET_PLATFORMS):
            continue

        # กฎข้อที่ 4: เช็ค Tactic ว่าตรงกับ 3 ตัวที่เราต้องการหรือไม่
        tactics = []
        for phase in obj.get("kill_chain_phases", []):
            if phase.get("kill_chain_name") == "mitre-attack":
                tactics.append(phase.get("phase_name"))

        matched_tactics = set(tactics).intersection(TARGET_TACTICS)
        if not matched_tactics:
            continue

        # ดึง Technique ID (เช่น T1110)
        technique_id = None
        for ext_ref in obj.get("external_references", []):
            if ext_ref.get("source_name") == "mitre-attack":
                technique_id = ext_ref.get("external_id")
                break

        if not technique_id:
            continue

        # 3. นำข้อมูลที่ผ่านการกรองทั้งหมด มาจัดรูปแบบให้คลีนขึ้น
        processed_techniques.append({
            "technique_id": technique_id,
            "technique_name": obj.get("name"),
            "tactic": list(matched_tactics)[0], # เก็บ Tactic หลัก
            "description": obj.get("description", ""), # ดึงคำอธิบายสำหรับทำ RAG
            "platforms": list(platforms)
        })

    # 4. สร้างโฟลเดอร์ data/processed/ หากยังไม่มี
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)

    # 5. บันทึกข้อมูลที่กรองเสร็จแล้วลงไฟล์ใหม่
    with open(PROCESSED_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(processed_techniques, f, indent=4, ensure_ascii=False)

    print(f"สำเร็จ! กรอง Technique ที่ตรงเงื่อนไขได้ทั้งหมด {len(processed_techniques)} เทคนิค")
    print(f"บันทึกไฟล์ใหม่เรียบร้อยที่: {PROCESSED_DATA_PATH}")

if __name__ == "__main__":
    process_stix_data()