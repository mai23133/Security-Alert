import json

from src.agents.gemini_client import generate_text
from src.schemas import ParsedAlert, TechniqueCandidate, InferredTechnique

# กำหนด System Prompt ที่ชัดเจนและบังคับโครงสร้างผลลัพธ์
SYSTEM_PROMPT = """You are an expert SOC analyst mapping security alerts to MITRE ATT&CK techniques.
You will be provided with a parsed security alert and a list of candidate techniques.
Your task is to select 1 to 3 techniques from the candidates that BEST match the alert.

For each selected technique, you MUST extract exact substrings from the Alert Narrative as 'evidence_spans' to justify your selection. 
The evidence MUST be an exact quote from the input narrative.

Respond STRICTLY in JSON array format, where each object matches this schema:
[
  {
    "technique_id": "TXXXX",
    "confidence": 0.95,
    "evidence_spans": ["exact quote from narrative 1", "exact quote 2"]
  }
]
Do not hallucinate technique IDs. Only use IDs from the provided candidate list.
"""

def infer_techniques(alert: ParsedAlert, candidates: list[TechniqueCandidate]) -> list[InferredTechnique]:
    """
    วิเคราะห์และเลือก Technique ID จาก Candidate ที่ได้รับ พร้อมดึง Evidence
    """
    # 1. ตรวจสอบว่ามี Candidate หรือไม่
    if not candidates:
        return []

    # 2. เตรียมข้อมูล Candidate ให้อยู่ในรูปแบบที่ LLM อ่านง่าย
    candidates_text = "\n".join(
        [f"- {c.technique_id}: {c.technique_name} (Tactic: {c.tactic})\n  Desc: {c.description_excerpt}" 
         for c in candidates]
    )

    # 3. เตรียมข้อมูล Alert
    alert_content = f"""
Narrative: {alert.narrative}
Assets: {alert.assets}
Actions: {alert.observed_actions}
IOCs: {alert.iocs}
"""

    # 4. ประกอบร่าง Prompt
    full_prompt = f"""{SYSTEM_PROMPT}

## CANDIDATE TECHNIQUES
{candidates_text}

## SECURITY ALERT
{alert_content}
"""

    inferred_results = []
    
    try:
        # 5. เรียกใช้ Gemini โดยเปิดโหมด JSON (is_json=True)
        raw_response = generate_text(full_prompt, is_json=True)
        parsed_json = json.loads(raw_response)
        
        if not isinstance(parsed_json, list):
            raise ValueError("LLM response is not a JSON array.")

        # 6. แมปผลลัพธ์จาก LLM เข้ากับข้อมูล Candidate เดิมเพื่อสร้าง InferredTechnique
        # สร้าง Dictionary สำหรับค้นหาข้อมูล Candidate อย่างรวดเร็ว
        candidate_map = {c.technique_id: c for c in candidates}

        for item in parsed_json:
            t_id = item.get("technique_id")
            
            # กรองเฉพาะ Technique ที่อยู่ใน Candidate จริงๆ (ป้องกัน Hallucination)
            if t_id in candidate_map:
                candidate = candidate_map[t_id]
                
                inferred_results.append(
                    InferredTechnique(
                        technique_id=t_id,
                        technique_name=candidate.technique_name,
                        tactic=candidate.tactic,
                        confidence=float(item.get("confidence", 0.0)),
                        evidence_spans=item.get("evidence_spans", []),
                        mitre_url=f"https://attack.mitre.org/techniques/{t_id.replace('.', '/')}"
                    )
                )
                
    except Exception as e:
        print(f"Error during technique inference: {e}")
        # หากเกิดข้อผิดพลาด จะส่ง List ว่างกลับไป เพื่อไม่ให้โปรแกรมหลักพัง
        return []

    return inferred_results

if __name__ == "__main__":
    # ตัวอย่างการรันทดสอบไฟล์นี้แบบ Standalone
    sample_alert = ParsedAlert(
        narrative="Host WIN-SRV-04 logged 847 failed RDP authentication attempts from IP 203.0.113.44, followed by a successful login and execution of encoded PowerShell.",
        assets=["WIN-SRV-04"],
        observed_actions=["failed RDP authentication", "successful login", "encoded PowerShell execution"],
        iocs=["203.0.113.44"]
    )
    
    sample_candidates = [
        TechniqueCandidate(
            technique_id="T1110",
            technique_name="Brute Force",
            tactic="credential-access",
            description_excerpt="Adversaries may use brute force techniques to gain access to accounts."
        ),
        TechniqueCandidate(
            technique_id="T1059.001",
            technique_name="Command and Scripting Interpreter: PowerShell",
            tactic="execution",
            description_excerpt="Adversaries may abuse PowerShell commands and scripts for execution."
        ),
        TechniqueCandidate(
            technique_id="T1548",
            technique_name="Abuse Elevation Control Mechanism",
            tactic="privilege-escalation",
            description_excerpt="Adversaries may circumvent mechanisms designed to control elevate privileges."
        )
    ]
    
    results = infer_techniques(sample_alert, sample_candidates)
    
    print("\n--- Inferred Techniques ---")
    for r in results:
        print(f"[{r.technique_id}] {r.technique_name} (Confidence: {r.confidence})")
        print(f"  Evidence: {r.evidence_spans}")
        print(f"  URL: {r.mitre_url}\n")