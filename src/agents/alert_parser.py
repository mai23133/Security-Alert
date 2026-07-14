"""
Alert Parser — Week 3 deliverable.
รับ narrative ข้อความดิบ แล้วแตกออกเป็น assets, observed_actions, iocs
ใช้ Google Gemini API (ฟรี)
"""
import json
import os
import google.generativeai as genai
from src.schemas import ParsedAlert

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-3.5-flash")

SYSTEM_PROMPT = """You are a security alert parser. Extract structured information from security alert narratives.
Return ONLY valid JSON matching this schema exactly — no explanation, no markdown:
{
  "narrative": "<original text>",
  "assets": ["<hostnames, IPs, systems mentioned>"],
  "observed_actions": ["<what happened, each action as a short phrase>"],
  "iocs": ["<IP addresses, hashes, domains, file paths>"]
}
Rules:
- assets: hostnames, server names, system names (e.g. "WIN-SRV-04")
- iocs: IP addresses, file hashes, domains, suspicious file paths
- observed_actions: verb phrases describing what happened (e.g. "847 failed RDP login attempts")
- If nothing found for a field, return an empty list []
"""

def parse_alert(narrative: str) -> ParsedAlert:
    """แตก narrative เป็น ParsedAlert struct"""
    response = model.generate_content(SYSTEM_PROMPT + "\n\nAlert:\n" + narrative)
    raw = response.text.strip()
    # ตัด markdown code block ออกถ้า Gemini ใส่มา
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    data["narrative"] = narrative  # ใช้ original เสมอ ไม่ใช้จาก LLM
    return ParsedAlert(**data)


if __name__ == "__main__":
    sample = (
        "Host WIN-SRV-04 logged 847 failed RDP authentication attempts "
        "from IP 203.0.113.44 between 02:00–04:00 UTC, followed by a "
        "successful login and execution of encoded PowerShell."
    )
    result = parse_alert(sample)
    print(result.model_dump_json(indent=2))