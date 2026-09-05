import json

from src.agents.gemini_client import generate_text
from src.schemas import ParsedAlert, InferredTechnique

# System Prompt สั่งให้ LLM ดึงเฉพาะข้อความที่มีอยู่จริงเป๊ะๆ เท่านั้น
SYSTEM_PROMPT = """You are a specialized Evidence Linker agent for a SOC pipeline.
Your task is to find the exact quotes in a security alert narrative that justify a specific MITRE ATT&CK technique.

Rules:
- You MUST return ONLY a JSON array of strings.
- Each string MUST be an EXACT, word-for-word substring from the original narrative.
- If there is no clear evidence in the text for the given technique, return an empty array [].
- Do not explain, do not paraphrase, and do not add any extra text.

Example Output:
["847 failed RDP authentication attempts", "execution of encoded PowerShell"]
"""

def extract_evidence(narrative: str, technique_id: str, technique_name: str) -> list[str]:
    """
    ให้ LLM ค้นหาประโยคหลักฐานสำหรับ 1 Technique
    """
    prompt = f"""{SYSTEM_PROMPT}

## Original Alert Narrative:
"{narrative}"

## Target Technique to find evidence for:
- ID: {technique_id}
- Name: {technique_name}
"""
    try:
        # เรียกใช้งาน Gemini โดยบังคับตอบเป็น JSON Array
        raw_response = generate_text(prompt, is_json=True)
        evidence_list = json.loads(raw_response)
        
        if isinstance(evidence_list, list):
            return evidence_list
        else:
            return []
            
    except Exception as e:
        print(f"Error extracting evidence for {technique_id}: {e}")
        return []

def link_evidence_to_techniques(alert: ParsedAlert, techniques: list[InferredTechnique]) -> list[InferredTechnique]:
    """
    วนลูปนำ Technique ที่ Inferencer เลือกไว้ มาหาข้อความอ้างอิง (Evidence Spans)
    """
    for tech in techniques:
        # หาก Technique ไหนยังไม่มี Evidence ให้ทำการค้นหา
        if not tech.evidence_spans:
            print(f"🔍 Linking evidence for {tech.technique_id}...")
            found_spans = extract_evidence(
                narrative=alert.narrative, 
                technique_id=tech.technique_id, 
                technique_name=tech.technique_name
            )
            tech.evidence_spans = found_spans
            
    return techniques

if __name__ == "__main__":
    # --- ตัวอย่างการทดสอบ Evidence Linker ---
    sample_alert = ParsedAlert(
        narrative="Host WIN-SRV-04 logged 847 failed RDP authentication attempts from IP 203.0.113.44, followed by a successful login and execution of encoded PowerShell.",
        assets=["WIN-SRV-04"],
        observed_actions=["failed RDP authentication", "encoded PowerShell execution"],
        iocs=["203.0.113.44"]
    )
    
    # สมมติว่า Inferencer เลือก 2 เทคนิคนี้มา แต่ยังไม่มี evidence_spans
    sample_inferred = [
        InferredTechnique(
            technique_id="T1110",
            technique_name="Brute Force",
            tactic="credential-access",
            confidence=0.95,
            evidence_spans=[], 
            mitre_url="https://attack.mitre.org/techniques/T1110/"
        ),
        InferredTechnique(
            technique_id="T1059.001",
            technique_name="Command and Scripting Interpreter: PowerShell",
            tactic="execution",
            confidence=0.90,
            evidence_spans=[], 
            mitre_url="https://attack.mitre.org/techniques/T1059/001/"
        )
    ]

    print("\n--- Running Evidence Linker ---")
    linked_results = link_evidence_to_techniques(sample_alert, sample_inferred)
    
    for r in linked_results:
        print(f"\n[{r.technique_id}] {r.technique_name}")
        print(f"Found Evidence: {r.evidence_spans}")