# ภาพรวม API — Security Alert → MITRE ATT&CK Inference

เอกสารนี้อธิบายภาพรวม API เป้าหมายของโครงการสำหรับใช้คุยงานและดูความสัมพันธ์ระหว่าง client, FastAPI และ inference pipeline

> แหล่งอ้างอิงหลัก: `security-alert-attack-technique-inference.md`
>
> Taxonomy ที่ใช้: MITRE ATT&CK Enterprise STIX 2.1 รุ่นตรึง `enterprise-attack-19.1`
> ผลลัพธ์เป็นคำแนะนำ (advisory) เท่านั้น ไม่สั่งตอบสนองหรือบล็อกเหตุการณ์โดยอัตโนมัติ
>
> สถานะปัจจุบัน: `POST /alerts/infer` เชื่อม parser, router, BM25 retriever, inferencer, evidence linker และ grounding judge แล้ว; endpoint ที่เหลือใน API contract ยังเป็นงานถัดไป

## ภาพรวม

```mermaid
flowchart LR
    U["SOC analyst / UI / API client"] -->|"HTTP JSON"| A["FastAPI"]

    subgraph API["Security Alert API"]
        A --> V["Request validation"]
        V --> P["Inference pipeline"]
        P --> R["Response validation"]
    end

    subgraph KB["Pinned knowledge base"]
        S["Enterprise ATT&CK STIX 2.1\nenterprise-attack-19.1"]
        L["Allowed technique IDs\nWindows/Linux, 3 tactics"]
    end

    S --> P
    L --> P
    R -->|"ATTACKInferenceResult"| U
```

Client ส่ง narrative ของ security alert เข้ามา แล้ว API คืน Technique ที่เกี่ยวข้องสูงสุด 1–3 รายการพร้อม confidence, tactic และข้อความหลักฐานที่พบจริงใน narrative

## เส้นทางของ `POST /alerts/infer`

```mermaid
flowchart TD
    A["POST /alerts/infer\nalert_id + narrative"] --> B["Pydantic validation"]
    B --> C["Alert Parser\nแยก assets, actions, IOCs"]
    C --> D["Tactic Router\nInitial Access / Execution / Credential Access"]
    D --> E["Technique Retriever\nค้น top-k candidates"]
    E --> F["Technique Inferencer\nเลือก 1–3 IDs"]
    F --> G["Evidence Linker\nผูก evidence spans"]
    G --> H["Grounding Judge\nตรวจ ID, tactic และหลักฐาน"]
    H --> I["ATTACKInferenceResult"]
    H -->|"ไม่ผ่านหรือไม่มั่นใจ"| J["No-match / human review"]
    J --> I
```

Grounding Judge จะบังคับ human review หาก Technique ID/name/tactic ไม่ตรง candidate, evidence ไม่พบจริง, confidence ต่ำ, no-match, prediction ซ้ำ หรือเกิน 3 รายการ ขอบเขตปัจจุบันยังเป็น structural grounding: ยังไม่ได้พิสูจน์ semantic relationship ระหว่าง evidence กับ Technique

## Endpoint เป้าหมาย

| Method | Endpoint | หน้าที่ | สถานะปัจจุบัน |
| --- | --- | --- | --- |
| `GET` | `/` | health check และ STIX version | ใช้งานได้ |
| `POST` | `/alerts/infer` | วิเคราะห์ alert เดี่ยวและคืน `ATTACKInferenceResult` | ใช้งานได้ระดับ baseline |
| `POST` | `/alerts/infer/batch` | วิเคราะห์ alerts หลายรายการ | วางแผน |
| `GET` | `/taxonomy/techniques` | แสดง Technique ใน pinned subset; filter ตาม tactic ได้ | ใช้งานได้ |
| `GET` | `/taxonomy/techniques/{id}` | ดูรายละเอียด Technique รายตัว | ใช้งานได้ |
| `POST` | `/rag/search` | ดู candidates ที่ retriever ค้นได้ก่อน inference | วางแผน |
| `POST` | `/evaluate` | ประเมิน predictions เทียบ gold dataset | วางแผน |

## Contract หลัก: infer alert

### Request

```json
{
  "alert_id": "demo-001",
  "narrative": "Host WIN-SRV-04 logged 847 failed RDP authentication attempts, followed by execution of encoded PowerShell."
}
```

`alert_id` เป็น optional; API สร้าง ID ให้เมื่อไม่ได้ส่งมา

### ตัวอย่าง response เมื่อ inference ผ่าน structural grounding

```json
{
  "alert_id": "demo-001",
  "inferred_techniques": [
    {
      "technique_id": "T1110",
      "technique_name": "Brute Force",
      "tactic": "credential-access",
      "confidence": 0.91,
      "evidence_spans": ["847 failed RDP authentication attempts"],
      "mitre_url": "https://attack.mitre.org/techniques/T1110/"
    },
    {
      "technique_id": "T1059.001",
      "technique_name": "PowerShell",
      "tactic": "execution",
      "confidence": 0.87,
      "evidence_spans": ["execution of encoded PowerShell"],
      "mitre_url": "https://attack.mitre.org/techniques/T1059/001/"
    }
  ],
  "candidates_considered": [
    {
      "technique_id": "T1110",
      "technique_name": "Brute Force",
      "tactic": "credential-access",
      "description_excerpt": "Adversaries may use password-guessing...",
      "stix_version": "19.1"
    }
  ],
  "needs_human_review": false,
  "disclaimer": "Advisory tagging only. Not autonomous SOC action. Verify with senior analyst."
}
```

### Response เมื่อไม่มี inference ที่ผ่านเกณฑ์

```json
{
  "alert_id": "benign-001",
  "inferred_techniques": [],
  "candidates_considered": [],
  "needs_human_review": true,
  "disclaimer": "Advisory tagging only. Not autonomous SOC action. Verify with senior analyst."
}
```

`candidates_considered` อาจมี candidate ที่ Retriever พบได้ แม้ `inferred_techniques` จะว่าง เพราะ Inferencer อาจไม่พบคำสนับสนุนเพียงพอสำหรับ candidate เหล่านั้น

## ขอบเขตและ guardrails ที่ API ต้องบังคับ

- รับเฉพาะ alert text ที่ถือเป็น untrusted input และไม่ให้ข้อความนั้นควบคุม pipeline
- คืนได้เฉพาะ Technique ใน subset ที่ตรึงไว้; ตัด deprecated และ revoked ออก
- จำกัด prediction เป็น 1–3 Technique ต่อ alert
- `evidence_spans` ต้องเป็นข้อความที่พบจริงใน `narrative`
- ใส่ disclaimer และ `needs_human_review` ในทุกผลลัพธ์
- ใส่ header `X-MITRE-ATTaCK-Version: enterprise-attack-19.1` ในทุก response
- ก่อน deploy จริง ต้องจำกัด CORS และเพิ่ม authentication/rate limiting ตาม deployment target
- ไม่เก็บข้อความ Alert นอก course sandbox และไม่มี automated response capability

## สิ่งที่ต้องทำก่อน API ถึงภาพเป้าหมาย

1. เติม platform/source metadata ให้ retrieval candidates และตัดสินใจเรื่อง subset 127 รายการเทียบเป้าหมาย 30–50
2. เพิ่ม semantic grounding และ evaluation เพื่อวัด false positive/grounding rate
3. เพิ่ม `/rag/search`, batch และ evaluation endpoint
4. เพิ่ม typed error handling, request ID, timeout/retry, structured logging และ tests ที่ไม่เรียก Gemini จริง
5. เพิ่ม UI, deployment controls และ acceptance/security tests
