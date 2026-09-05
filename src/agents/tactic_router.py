import json
import re

from src.agents.gemini_client import generate_text
from src.schemas import ParsedAlert

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

    raw = generate_text(SYSTEM_PROMPT + "\n\nAlert:\n" + content)
    
    try:
        # ใช้ Regex เพื่อค้นหาและดึงเฉพาะส่วนที่เป็น Array [...] ออกมา
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            json_str = match.group(0)
        else:
            json_str = raw.strip()
            
        tactics = json.loads(json_str)
        
        # ตรวจสอบว่าเป็น List จริงๆ
        if not isinstance(tactics, list):
            raise ValueError("Parsed JSON is not a list.")

        # Validate: กรองออกถ้า LLM ส่งนอก scope มา และเช็ค type
        valid = [t for t in tactics if isinstance(t, str) and t in IN_SCOPE_TACTICS]
        
        if valid:
            return valid
        else:
            print("Warning: LLM returned no valid tactics. Fallback to IN_SCOPE_TACTICS.")
            return IN_SCOPE_TACTICS

    except (json.JSONDecodeError, ValueError) as e:
        # Log error เพื่อการตรวจสอบ
        print(f"Error parsing Gemini response: {e}. Raw output: {raw}")
        return IN_SCOPE_TACTICS  # Fallback: ค้นทั้ง 3

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