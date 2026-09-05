from fastapi.testclient import TestClient
from src.api.main import app

# สร้าง TestClient สำหรับจำลองการยิง Request เข้า FastAPI
client = TestClient(app)

def test_read_root():
    """ทดสอบหน้าแรกว่าระบบสถานะปกติและคืนค่า STIX version ถูกต้อง"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "stix_version": "19.1"}
    # ตรวจสอบ Header MITRE Attribution ตามสเปก
    assert response.headers["x-mitre-attack-version"] == "enterprise-attack-19.1"

def test_infer_alert_success():
    """ทดสอบการส่ง Alert เดี่ยวในกรณีปกติ (Fake Success)"""
    response = client.post("/alerts/infer", json={"narrative": "พบการพยายามล็อกอินรหัสผ่านซ้ำๆ"})
    assert response.status_code == 200
    data = response.json()
    
    # ตรวจสอบโครงสร้างผลลัพธ์ว่ามีฟิลด์สำคัญครบถ้วนตาม Schema
    assert "request_id" in data
    assert "prediction" in data
    assert "confidence" in data
    assert "evidence_spans" in data
    assert data["needs_human_review"] is True
    assert "disclaimer" in data

def test_batch_infer_alerts():
    """ทดสอบการส่ง Alert แบบกลุ่ม (Batch Endpoint)"""
    payload = {
        "alerts": [
            {"narrative": "Alert ตัวที่ 1 ทดสอบระบบ"},
            {"narrative": "Alert ตัวที่ 2 ทดสอบระบบ"}
        ]
    }
    response = client.post("/alerts/batch-infer", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # ตรวจสอบว่าผลลัพธ์ตีกลับมาเป็นอาเรย์ของ results ครบ 2 รายการ
    assert "results" in data
    assert len(data["results"]) == 2
    assert "prediction" in data["results"][0]