import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# 1. โครงสร้างข้อมูล (Schemas)

class AlertRequest(BaseModel):
    alert_id: Optional[str] = None
    narrative: str

class ATTACKInferenceResult(BaseModel):
    request_id: str
    prediction: List[str]
    confidence: str
    evidence_spans: List[str]
    needs_human_review: bool
    candidates: List[str]
    disclaimer: str = "Advisory only. Needs human review. MITRE attribution."

class BatchAlertRequest(BaseModel):
    alerts: List[AlertRequest]

class BatchInferenceResult(BaseModel):
    results: List[ATTACKInferenceResult]

# 2. ท่อส่งข้อมูลจำลอง (Fake Inference Pipeline)
def fake_inference_pipeline(narrative: str) -> dict:
    if "timeout" in narrative.lower():
        raise TimeoutError("Simulated provider timeout")
    if "error" in narrative.lower():
        raise ValueError("Simulated provider error")
    
    return {
        "prediction": ["T1110"],
        "confidence": "High",
        "evidence_spans": ["failed RDP authentication attempts"],
        "needs_human_review": True,
        "candidates": ["T1110", "T1078", "T1133"]
    }
# 3. API Endpoints

# Endpoint สำหรับวิเคราะห์ 1 รายการ
@router.post("/infer", response_model=ATTACKInferenceResult)
def infer_alert(request: AlertRequest):
    req_id = request.alert_id if request.alert_id else str(uuid.uuid4())
    
    try:
        result = fake_inference_pipeline(request.narrative)
        return ATTACKInferenceResult(
            request_id=req_id,
            prediction=result["prediction"],
            confidence=result["confidence"],
            evidence_spans=result["evidence_spans"],
            needs_human_review=result["needs_human_review"],
            candidates=result["candidates"]
        )
    except TimeoutError:
        raise HTTPException(status_code=504, detail={"request_id": req_id, "error": "Request Timeout"})
    except Exception:
        raise HTTPException(status_code=500, detail={"request_id": req_id, "error": "Internal Processing Error"})

# Endpoint สำหรับวิเคราะห์หลายรายการพร้อมกัน (Batch)
@router.post("/infer/batch", response_model=BatchInferenceResult)
def batch_infer_alerts(request: BatchAlertRequest):
    batch_results = []
    
    for alert in request.alerts:
        req_id = alert.alert_id if alert.alert_id else str(uuid.uuid4())
        try:
            result = fake_inference_pipeline(alert.narrative)
            batch_results.append(
                ATTACKInferenceResult(
                    request_id=req_id,
                    prediction=result["prediction"],
                    confidence=result["confidence"],
                    evidence_spans=result["evidence_spans"],
                    needs_human_review=result["needs_human_review"],
                    candidates=result["candidates"]
                )
            )
        except Exception as e:
            # กรณีพังเฉพาะบางตัว ให้คืนค่า Safe Error ตัวนั้นๆ เพื่อไม่ให้ล่มทั้งระบบ
            batch_results.append(
                ATTACKInferenceResult(
                    request_id=req_id,
                    prediction=["System Error"],
                    confidence="None",
                    evidence_spans=[str(e)],
                    needs_human_review=True,
                    candidates=[]
                )
            )
            
    return BatchInferenceResult(results=batch_results)