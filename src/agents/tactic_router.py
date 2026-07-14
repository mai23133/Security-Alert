"""
Tactic Router — Week 3 deliverable.
รับ ParsedAlert แล้วทายว่าน่าจะเข้า tactic ไหนใน 3 ตัวที่อยู่ใน scope
ใช้ Google Gemini API (ฟรี)
"""
import json
import os
import google.generativeai as genai
from src.schemas import ParsedAlert

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-3.5-flash")

IN_SCOPE_TACTICS = ["initial-access", "execution", "credential-access"]

SYSTEM_PROMPT = f"""You are a MITRE ATT&CK tactic classifier for security alerts.
Given a parsed security alert, predict which of these tactics are relevant:
{json.dumps(IN_SCOPE_TACTICS)}

Definitions:
- initial-access: attacker gaining first foothold (phishing, exploit public-facing app, valid accounts from external)
- execution: attacker running malicious code (scripts, scheduled tasks, command interpreters)
- credential-access: stealing credentials (brute force, credential dumping, keylogging)

Return ONLY a JSON array of matching tactic strings — no explanation, no markdown.
Example: ["credential-access", "execution"]
Rules:
- Return 1–3 tactics only from the list above
- If uncertain, include the most likely one
- Never return tactics outside the list
"""

def route_tactics(alert: ParsedAlert) -> list[str]:
    """ทาย tactic ที่น่าจะเกี่ยวข้องจาก ParsedAlert"""
    content = f"""Assets: {alert.assets}
Actions: {alert.observed_actions}
IOCs: {alert.iocs}
Narrative: {alert.narrative}"""

    response = model.generate_content(SYSTEM_PROMPT + "\n\nAlert:\n" + content)
    raw = response.text.strip()
    # ตัด markdown code block ออกถ้า Gemini ใส่มา
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    tactics = json.loads(raw.strip())

    # validate — กรองออกถ้า LLM ส่งนอก scope มา
    valid = [t for t in tactics if t in IN_SCOPE_TACTICS]
    return valid if valid else IN_SCOPE_TACTICS  # fallback: ค้นทั้ง 3


if __name__ == "__main__":
    from src.agents.alert_parser import parse_alert
    sample = (
        "Host WIN-SRV-04 logged 847 failed RDP authentication attempts "
        "from IP 203.0.113.44 between 02:00–04:00 UTC, followed by a "
        "successful login and execution of encoded PowerShell."
    )
    alert = parse_alert(sample)
    tactics = route_tactics(alert)
    print("Predicted tactics:", tactics)