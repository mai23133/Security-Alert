import json
from pydantic import ValidationError

from src.agents.gemini_client import generate_text
from src.schemas import ParsedAlert

# ตัด "narrative" ออกจาก Schema ใน Prompt เพื่อประหยัด Token เพราะเราจะใส่กลับไปเอง
SYSTEM_PROMPT = """You are a security alert parser. Extract structured information from security alert narratives.
Return ONLY valid JSON matching this schema exactly — no explanation, no markdown:
{
  "assets": ["<hostnames, IPs, systems mentioned>"],
  "observed_actions": ["<what happened, each action as a short phrase>"],
  "iocs": ["<IP addresses, domains, file hashes, paths>"]
}
Rules:
- assets: hostnames, server names, system names (e.g. "WIN-SRV-04")
- iocs: IP addresses, file hashes, domains, suspicious file paths
- observed_actions: verb phrases describing what happened (e.g. "847 failed RDP login attempts")
- If nothing found for a field, return an empty list []
"""

def parse_alert(narrative: str) -> ParsedAlert:
    """แตก narrative เป็น ParsedAlert struct"""
    raw_response = ""
    try:
        # 1. เรียกใช้งานแบบบังคับ JSON Mode ทันที
        raw_response = generate_text(SYSTEM_PROMPT + "\n\nAlert:\n" + narrative, is_json=True)
        data = json.loads(raw_response)
        
        # 2. ป้องกันกรณี LLM แอบใส่ narrative กลับมา ให้ลบทิ้งไปก่อน
        if "narrative" in data:
            del data["narrative"]
            
        # 3. ยัด Original Narrative กลับเข้าไป และ Map เข้า Pydantic Model
        return ParsedAlert(narrative=narrative, **data)
        
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Error parsing alert: {e}. Raw LLM output: {raw_response}")
        # Fallback: หากพัง ให้คืนค่าโครงสร้างเปล่าๆ กลับไปพร้อมแจ้งเตือน
        return ParsedAlert(
            narrative=narrative,
            assets=[],
            observed_actions=["Error: Failed to parse actions"],
            iocs=[]
        )

if __name__ == "__main__":
    sample = (
        "Host WIN-SRV-04 logged 847 failed RDP authentication attempts "
        "from IP 203.0.113.44 between 02:00–04:00 UTC, followed by a "
        "successful login and execution of encoded PowerShell."
    )
    result = parse_alert(sample)
    # แสดงผลออกมาเป็น JSON สวยงาม
    print(result.model_dump_json(indent=2))