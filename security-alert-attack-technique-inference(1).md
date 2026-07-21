# Security Alert → ATT&CK Technique Inference

## 1. Problem Statement

Security analysts receive alert narratives, SIEM summaries, and incident notes in free text. Mapping these to a standardized threat taxonomy is slow, inconsistent, and requires deep ATT&CK knowledge.

**Product goal:** Given a security alert or incident narrative, retrieve relevant MITRE ATT&CK techniques from the official knowledge base and **infer** the most likely technique ID(s) with evidence spans and confidence — advisory only, not autonomous SOC response.

**Pattern:** RAG + zero-shot inference (same shape as clinical coding, but using public ATT&CK taxonomy).

## 2. Users & Use Cases

- **SOC Tier-1 analyst** — gets suggested ATT&CK technique tags with citations before escalation.
- **Threat intel trainee** — practices mapping synthetic scenarios to the Enterprise matrix.
- **Detection engineer** — validates alert coverage against technique labels.

## 3. In Scope / Out of Scope

**In scope:**

- Free-text alert/incident narrative input (synthetic, instructor-provided)
- RAG over **pinned MITRE ATT&CK Enterprise STIX 2.1** release
- Infer 1–3 technique IDs per alert (multi-label)
- Structured output: technique ID, name, confidence, evidence spans, tactic
- Subset scope: **Initial Access, Execution, Credential Access** tactics (~30–50 techniques)
- Exclude deprecated/revoked techniques from inference candidates
- Judge agent enforcing evidence grounding

**Out of scope:**

- Autonomous incident response or blocking actions
- Full Enterprise matrix (~600+ techniques) without subsetting
- Mobile or ICS ATT&CK domains
- Live TAXII ingestion as grading dependency (optional stretch goal only)
- Malware binary analysis or PCAP inspection

## 4. Source of Truth (Taxonomy)

| Layer | Source | URL |
| --- | --- | --- |
| **Canonical codebook** | MITRE ATT&CK STIX 2.1 JSON (pinned) | `enterprise-attack-19.1.json` from attack-stix-data |
| Human reference | MITRE technique pages | https://attack.mitre.org/techniques/enterprise/ |
| Live feed (optional) | TAXII 2.1 | https://attack-taxii.mitre.org/api/v21/ |
| **Eval gold labels** | Instructor synthetic alerts | Bundled with course data pack |

**Pinned version for course:** `enterprise-attack-19.1` (lock at semester start; all groups use same file).

**Technique ID format:** `T####` or `T####.###` (sub-techniques). Example: `T1110` Brute Force, `T1059.001` PowerShell.

**Key STIX fields for RAG indexing:**

- `external_id` → technique ID
- `name`, `description`
- `kill_chain_phases` → tactics
- `x_mitre_platforms` → platform filter
- `x_mitre_deprecated`, `revoked` → exclude from candidates

## 5. Agent Architecture (Mixture of Experts)

```mermaid
flowchart LR
    A[Alert Parser] --> B[Tactic Router]
    B --> C[Technique Retriever RAG]
    C --> D[Technique Inferencer]
    D --> E[Evidence Linker]
    E --> F[Grounding Judge]
```

| Agent | Responsibility |
| --- | --- |
| **Alert Parser** | Normalize narrative; extract IOCs, actions, assets (structured) |
| **Tactic Router** | Predict likely tactics to narrow retrieval (e.g. credential-access) |
| **Technique Retriever** | Hybrid RAG over pinned STIX subset; return top-k candidates |
| **Technique Inferencer** | Zero-shot select 1–3 technique IDs from candidates |
| **Evidence Linker** | Map each technique to quoted spans in input text |
| **Grounding Judge** | Reject techniques without input evidence; reject hallucinated IDs |

## 6. Data Schemas (Pydantic)

```python
class ParsedAlert(BaseModel):
    narrative: str
    assets: list[str]
    observed_actions: list[str]
    iocs: list[str]

class TechniqueCandidate(BaseModel):
    technique_id: str          # e.g. "T1110"
    technique_name: str
    tactic: str
    description_excerpt: str
    stix_version: str          # e.g. "19.1"

class InferredTechnique(BaseModel):
    technique_id: str
    technique_name: str
    tactic: str
    confidence: float
    evidence_spans: list[str]  # quotes from input
    mitre_url: str

class ATTACKInferenceResult(BaseModel):
    alert_id: str
    inferred_techniques: list[InferredTechnique]
    candidates_considered: list[TechniqueCandidate]
    needs_human_review: bool
    disclaimer: str
```

## 7. Knowledge Base (Instructor Provides)

**From MITRE (public):**

- Pinned `enterprise-attack-19.1.json`
- Pre-filtered subset JSON: 3 tactics, Windows + Linux platforms, deprecated/revoked removed

**Instructor-authored (eval SoT):**

- **35 synthetic alert narratives** with gold technique labels (1–3 per alert)
- 10 ambiguous / multi-technique edge cases
- 5 negative controls (benign activity → no technique or observation only)
- Technique subset manifest (`technique_ids.json`)

**Example alert input:**

> "Host WIN-SRV-04 logged 847 failed RDP authentication attempts from IP 203.0.113.44 between 02:00–04:00 UTC, followed by a successful login and execution of encoded PowerShell."

**Gold label:** `T1110` (Brute Force), `T1059.001` (PowerShell)

## 8. API Contract (FastAPI)

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/alerts/infer` | Narrative text → `ATTACKInferenceResult` |
| POST | `/alerts/infer/batch` | Batch inference |
| GET | `/taxonomy/techniques` | List in-scope techniques (subset) |
| GET | `/taxonomy/techniques/{id}` | Technique detail from pinned STIX |
| POST | `/rag/search` | Debug: retrieve candidates for a query |
| POST | `/evaluate` | Run metrics vs gold labels |

## 9. Evaluation Pack

| Metric | Description |
| --- | --- |
| **Exact technique F1** | Predicted IDs vs gold (multi-label) |
| **Parent technique recall** | Partial credit: `T1059.001` → `T1059` |
| **Evidence grounding rate** | Judge confirms spans support each ID |
| **Hallucinated ID rate** | IDs not in pinned subset or not in STIX |
| **False-positive rate** | Techniques assigned to benign controls |

**Pass threshold (demo):** ≥70% exact F1 on gold set (subset), ≥90% parent recall, 0 hallucinated IDs, ≥85% evidence grounding.

**Grading note:** Eval labels are instructor SoT; taxonomy definitions are MITRE SoT.

## 10. Security & Guardrails

- Treat alert text as **untrusted input** (prompt injection in log fields)
- **Disclaimer on every response:** "Advisory tagging only. Not autonomous SOC action. Verify with senior analyst."
- Never invent technique IDs — must exist in pinned STIX subset
- Require MITRE attribution + version string in API metadata
- No retention of alert text beyond course sandbox (configurable)

## 11. Milestone Mapping

แผนนี้ใช้กรอบเวลา 6 สัปดาห์ โดยเริ่มวันที่ 20 กรกฎาคม 2026 และให้ `WORK_PLAN_TH.md` เป็นแหล่งอ้างอิงหลักสำหรับสถานะงานล่าสุด

| Week | Date | Priority | Main work | Weekly acceptance checkpoint |
| --- | --- | --- | --- | --- |
| 1 | 20–26 Jul 2026 | P0 | Rotate exposed secrets, stop tracking `.env`, remove tracked bytecode, fix STIX ingestion output path, add setup documentation, pin dependencies, and add initial schema/ingestion/taxonomy API tests | Clean installation succeeds; no secrets or generated bytecode are tracked; STIX ingestion writes to `data/processed/`; initial tests pass |
| 2 | 27 Jul–2 Aug 2026 | P1 | Select and document the embedding backend and index format; update schemas for multiple tactics; implement `embedder.py`; build a metadata-rich index; implement `retriever.py` with tactic filtering and configurable top-k; add retrieval tests and an initial Recall@k evaluation set | Retriever returns reproducible top-k candidates from the pinned ATT&CK subset only, with tactic/platform/source metadata and baseline Recall@1, Recall@3, and Recall@5 results |
| 3 | 3–9 Aug 2026 | P1 | Implement `technique_inferencer.py` with structured output, `evidence_linker.py`, and `grounding_judge.py`; define confidence and `needs_human_review` rules; test prompt injection and malformed model output | Every prediction is selected only from retrieved candidates, includes traceable evidence, passes grounding checks, and routes uncertain or no-match cases to human review |
| 4 | 10–16 Aug 2026 | P1–P2 | Connect the real pipeline to `POST /alerts/infer`; remove hard-coded technique results; add validation, timeout, retry, typed error handling, prompt loading/versioning, mocked unit/integration/API tests, structured logging, and request IDs | `/alerts/infer` uses the real end-to-end pipeline; failures are handled safely; tests are deterministic and do not call Gemini live |
| 5 | 17–23 Aug 2026 | P1–P2 | Build the labeled evaluation dataset covering positive, multi-technique, ambiguous, and no-match cases; implement evaluation metrics and runner; record model/prompt/dataset/STIX versions; add CI and an evaluation smoke test; define measurable MVP quality gates | CI passes and produces a reproducible versioned report containing exact precision/recall/F1, top-k recall, tactic accuracy, grounding results, hallucinated-ID rate, and human-review rate |
| 6 | 24–30 Aug 2026 | P1–P2 | Build the analyst UI for alert input, predictions, confidence, evidence, and review; restrict CORS and add deployment-appropriate authentication/rate limiting; define privacy and retention rules; add MITRE attribution, disclaimer, and license; package/deploy and run acceptance/security tests | The complete workflow works end to end and the release candidate passes acceptance and security checks with required attribution, privacy controls, and advisory messaging |

### Milestone dependencies

1. Week 1 establishes a clean, reproducible repository and valid pinned ATT&CK data.
2. Week 2 builds retrieval and must finish before inference agents are implemented.
3. Week 3 produces grounded inference components required by the API integration.
4. Week 4 completes the functional inference pipeline and automated tests.
5. Week 5 measures quality and prevents regressions before release.
6. Week 6 completes the analyst-facing workflow, deployment controls, and final verification.

## 12. Demo Script (3 min)

1. Submit brute-force + PowerShell alert → `T1110`, `T1059.001` with evidence quotes
2. Show RAG retrieval of top-5 candidate techniques before inference
3. Submit benign patch-management alert → no technique or low-confidence + review flag
4. Judge rejects technique when evidence span is removed (live demo of grounding)
5. Present eval dashboard: F1, parent recall, hallucination rate

## 13. Stretch Goals (Optional)

- TAXII live sync with pinned fallback
- ATT&CK Navigator layer export JSON
- Sub-technique vs parent-technique disambiguation agent
- Map to data components / detection strategies (ATT&CK v18+)

## 14. Dataset

### Instructor bundle (eval SoT)

- Pinned `enterprise-attack-19.1.json` + pre-filtered subset (3 tactics, Windows + Linux, deprecated/revoked removed)
- **35 synthetic alert narratives** with gold technique labels (1–3 per alert)
- 10 ambiguous / multi-technique edge cases
- 5 negative controls (benign activity → no technique)
- Technique subset manifest (`technique_ids.json`)

### Selected sources (added)

| Source | URL | Use for |
| --- | --- | --- |
| **MITRE attack-stix-data** | github.com/mitre-attack/attack-stix-data | Canonical STIX 2.1 taxonomy — pin `enterprise-attack-19.1.json` |
| **MITRE ATT&CK technique pages** | attack.mitre.org/techniques/enterprise | Human-readable descriptions for RAG indexing |
| **OTRF Security-Datasets** | github.com/OTRF/Security-Datasets | Real attack scenarios → convert to synthetic alert narratives |

### Additional public sources

| Source | URL | Use for |
| --- | --- | --- |
| **MITRE TAXII 2.1** (optional) | attack-taxii.mitre.org/api/v21 | Live feed — stretch goal only; pinned JSON is grading SoT |
| **Sigma rules** | github.com/SigmaHQ/sigma | Alert descriptions mappable to techniques |
| **Mordor** | github.com/OTRF/mordor | Attack replay datasets → narrative generation |
| **Atomic Red Team** | github.com/redcanaryco/atomic-red-team | Technique descriptions for synthetic alert authoring |
| **Splunk BOTS** | splunk.com — BOTS data | SOC-style alert text for realism |

### Synthetic / instructor-authored (eval gold)

- Write 35 alert narratives from technique descriptions — include brute-force + PowerShell, ambiguous multi-technique, and benign controls
- Gold labels are instructor SoT; taxonomy definitions are MITRE SoT
- Example: "847 failed RDP auth attempts… encoded PowerShell" → `T1110`, `T1059.001`

### Build strategy

> 💡 **Most self-contained data pack.** Public STIX for the KB; instructor-authored alerts for eval. Mordor/Sigma/BOTS can inspire narrative phrasing but eval gold must be instructor-labeled.

### Licensing & constraints

- Require MITRE attribution + version string in API metadata
- Never invent technique IDs — must exist in pinned STIX subset
- Treat alert text as untrusted input (prompt injection)
