from src.schemas import InferredTechnique

def evaluate_grounding(narrative: str, inferred_techniques: list[InferredTechnique]) -> tuple[list[InferredTechnique], bool]:
    """
    Grounding Judge: ตรวจสอบว่า Evidence Spans ถูกดึงมาจาก Narrative ต้นฉบับจริงๆ หรือไม่
    
    คืนค่ากลับเป็น Tuple:
    1. validated_techniques (List): รายการ Technique ที่ผ่านการตรวจสอบแล้ว
    2. needs_human_review (Bool): ค่าที่บอกว่าพบความผิดปกติและต้องให้ Analyst ตรวจสอบหรือไม่
    """
    needs_human_review = False
    validated_techniques = []

    # ปรับ Narrative ต้นฉบับให้เป็นตัวพิมพ์เล็กเพื่อลดปัญหาช่องว่าง/ตัวพิมพ์ผิดพลาดจากการประมวลผล
    narrative_lower = narrative.lower()

    for tech in inferred_techniques:
        valid_spans = []
        
        for span in tech.evidence_spans:
            # 1. เช็คว่ามีข้อความอ้างอิงนี้ในต้นฉบับจริงๆ หรือไม่
            if span.lower() in narrative_lower:
                valid_spans.append(span)
            else:
                # 2. พบ Hallucinated Evidence (LLM แต่งขึ้นมาเอง) -> แจ้งเตือน!
                print(f"[Grounding Alert] Hallucinated evidence removed for {tech.technique_id}: '{span}'")
                needs_human_review = True
        
        # อัปเดต Evidence Spans ให้เหลือเฉพาะอันที่ตรวจสอบแล้วว่าจริง
        tech.evidence_spans = valid_spans
        
        # 3. ตัดสิน Technique: หากเทคนิคนี้ไม่มี Evidence ที่ถูกต้องสนับสนุนเลย ให้ Reject ทิ้งไปเลย
        if not valid_spans:
            print(f"[Judge Reject] Technique {tech.technique_id} ({tech.technique_name}) rejected due to ZERO valid evidence.")
            needs_human_review = True
        else:
            validated_techniques.append(tech)

    # 4. หากไม่มี Technique ไหนผ่านเกณฑ์เลย ควรให้มนุษย์เข้ามาดู Alert นี้ด้วย
    if not validated_techniques:
        needs_human_review = True

    return validated_techniques, needs_human_review

if __name__ == "__main__":
    # --- ตัวอย่างการทดสอบ Grounding Judge ---
    sample_narrative = (
        "Host WIN-SRV-04 logged 847 failed RDP authentication attempts "
        "from IP 203.0.113.44 between 02:00–04:00 UTC, followed by a "
        "successful login and execution of encoded PowerShell."
    )
    
    sample_inferred = [
        # เคสที่ 1: ดึงข้อความมาถูกต้องเป๊ะ
        InferredTechnique(
            technique_id="T1110",
            technique_name="Brute Force",
            tactic="credential-access",
            confidence=0.98,
            evidence_spans=["847 failed RDP authentication attempts"],
            mitre_url="https://attack.mitre.org/techniques/T1110/"
        ),
        # เคสที่ 2: LLM แอบมั่วข้อความที่ไม่มีในต้นฉบับมาให้ (Hallucination)
        InferredTechnique(
            technique_id="T1059.001",
            technique_name="PowerShell",
            tactic="execution",
            confidence=0.85,
            evidence_spans=["execution of encoded PowerShell", "downloaded malware via web request"],
            mitre_url="https://attack.mitre.org/techniques/T1059/001/"
        )
    ]

    print("\n--- Running Grounding Judge ---")
    final_techniques, review_flag = evaluate_grounding(sample_narrative, sample_inferred)
    
    print(f"\nNeeds Human Review: {review_flag}")
    print("Final Approved Techniques:")
    for t in final_techniques:
        print(f"- {t.technique_id}: {t.evidence_spans}")