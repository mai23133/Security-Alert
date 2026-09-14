import { useState } from "react";

// ─── Sample data ───────────────────────────────────────────────────────────
const SAMPLES = [
  {
    label: "🚨 Brute-Force + PS",
    text: `ALERT [HIGH] WIN-SRV-04 | 2024-01-15T03:47:22Z
Source IP: 203.0.113.44 | Dest: 10.0.0.22:445
Event: 847 consecutive authentication failures on SMB over 4 minutes.
Post-auth: execution of encoded PowerShell command via cmd.exe:
  powershell -enc JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0AA==
Lateral movement observed to WIN-SRV-07 via PsExec within 90 seconds.
Process tree: explorer.exe > cmd.exe > powershell.exe (unsigned)
Network: beaconing to 203.0.113.44:4444 every 30 seconds (C2 pattern).`,
  },
  {
    label: "🟢 Benign Patch",
    text: `ALERT [LOW] WIN-WKS-11 | 2024-01-15T09:15:00Z
Source: WSUS internal server (10.0.0.5)
Event: Windows Update agent initiated download of KB5034441.
Process: svchost.exe -k netsvcs (expected, signed Microsoft binary).
No lateral movement. No authentication anomalies. No external connections.
Update completed successfully. System restarted at 09:22:14Z.
All signatures verified. Asset owner notified.`,
  },
  {
    label: "⚠️ Incomplete Evidence",
    text: `ALERT [MEDIUM] LNX-DB-02 | 2024-01-15T14:33:07Z
Unusual process spawned: /tmp/.cache/run (executable, no file extension).
Parent: sshd | User: dbadmin | PID: 9142
No network connections captured in this log segment.
File hash unavailable — agent reporting lag.
Partial syscall trace: open(), mmap(), socket() observed.
Insufficient telemetry to determine intent. Requires further investigation.`,
  },
];

const INFERENCE_RESULTS: Record<number, InferenceResult> = {
  0: {
    techniques: [
      {
        id: "T1110.001",
        name: "Brute Force: Password Guessing",
        tactic: "Credential Access",
        tacticColor: "#8b5cf6",
        confidence: 97,
        evidence: ["847 consecutive authentication failures on SMB over 4 minutes"],
        mitreUrl: "https://attack.mitre.org/techniques/T1110/001/",
      },
      {
        id: "T1059.001",
        name: "Command and Scripting Interpreter: PowerShell",
        tactic: "Execution",
        tacticColor: "#ef4444",
        confidence: 92,
        evidence: ["execution of encoded PowerShell command via cmd.exe", "powershell -enc JABjAGwAaQBlAG4AdAAgAD0A..."],
        mitreUrl: "https://attack.mitre.org/techniques/T1059/001/",
      },
      {
        id: "T1021.002",
        name: "Remote Services: SMB/Windows Admin Shares",
        tactic: "Lateral Movement",
        tacticColor: "#f97316",
        confidence: 85,
        evidence: ["Lateral movement observed to WIN-SRV-07 via PsExec within 90 seconds"],
        mitreUrl: "https://attack.mitre.org/techniques/T1021/002/",
      },
    ],
    entities: {
      assets: ["WIN-SRV-04", "WIN-SRV-07", "WIN-WKS-11"],
      iocs: ["203.0.113.44", "203.0.113.44:4444"],
      actions: ["847 failed attempts", "encoded PowerShell execution", "PsExec lateral movement", "C2 beaconing every 30s"],
    },
    needsReview: true,
    reviewReason: "High-confidence multi-technique chain. Escalate immediately.",
    candidates: [
      { rank: 1, id: "T1110.001", name: "Password Guessing", score: 0.97 },
      { rank: 2, id: "T1059.001", name: "PowerShell", score: 0.92 },
      { rank: 3, id: "T1021.002", name: "SMB/Windows Admin Shares", score: 0.85 },
      { rank: 4, id: "T1055.001", name: "Process Injection: DLL", score: 0.61 },
      { rank: 5, id: "T1071.001", name: "Application Layer Protocol: Web", score: 0.54 },
    ],
  },
  1: {
    techniques: [],
    entities: {
      assets: ["WIN-WKS-11"],
      iocs: ["10.0.0.5"],
      actions: ["Windows Update KB5034441", "WSUS download", "scheduled restart"],
    },
    needsReview: false,
    reviewReason: "No actionable malicious technique detected. Benign patch activity confirmed.",
    candidates: [
      { rank: 1, id: "T1072", name: "Software Deployment Tools", score: 0.38 },
      { rank: 2, id: "T1195", name: "Supply Chain Compromise", score: 0.12 },
      { rank: 3, id: "T1078", name: "Valid Accounts", score: 0.09 },
      { rank: 4, id: "T1105", name: "Ingress Tool Transfer", score: 0.07 },
      { rank: 5, id: "T1059", name: "Command and Scripting", score: 0.04 },
    ],
  },
  2: {
    techniques: [
      {
        id: "T1059",
        name: "Command and Scripting Interpreter",
        tactic: "Execution",
        tacticColor: "#ef4444",
        confidence: 52,
        evidence: ["/tmp/.cache/run (executable, no file extension)", "syscall trace: open(), mmap(), socket()"],
        mitreUrl: "https://attack.mitre.org/techniques/T1059/",
      },
    ],
    entities: {
      assets: ["LNX-DB-02"],
      iocs: ["/tmp/.cache/run"],
      actions: ["anomalous process spawn", "socket() syscall", "agent reporting lag"],
    },
    needsReview: true,
    reviewReason: "Incomplete telemetry. Low-confidence inference. Manual triage required.",
    candidates: [
      { rank: 1, id: "T1059", name: "Command and Scripting", score: 0.52 },
      { rank: 2, id: "T1055", name: "Process Injection", score: 0.44 },
      { rank: 3, id: "T1036.005", name: "Masquerading: Match Legitimate Name", score: 0.39 },
      { rank: 4, id: "T1027", name: "Obfuscated Files", score: 0.31 },
      { rank: 5, id: "T1070.004", name: "File Deletion", score: 0.21 },
    ],
  },
};

interface Technique {
  id: string;
  name: string;
  tactic: string;
  tacticColor: string;
  confidence: number;
  evidence: string[];
  mitreUrl: string;
}

interface InferenceResult {
  techniques: Technique[];
  entities: { assets: string[]; iocs: string[]; actions: string[] };
  needsReview: boolean;
  reviewReason: string;
  candidates: { rank: number; id: string; name: string; score: number }[];
}

// ─── Evaluation data ───────────────────────────────────────────────────────
const EVAL_ROWS = [
  { id: "ALT-001", expected: "T1110.001", predicted: "T1110.001", match: "Exact", grounded: true },
  { id: "ALT-002", expected: "T1059.001", predicted: "T1059.001", match: "Exact", grounded: true },
  { id: "ALT-003", expected: "T1021.002", predicted: "T1021.002", match: "Exact", grounded: true },
  { id: "ALT-004", expected: "T1190", predicted: "T1190", match: "Exact", grounded: true },
  { id: "ALT-005", expected: "T1566.001", predicted: "T1566", match: "Parent", grounded: true },
  { id: "ALT-006", expected: "T1055.012", predicted: "T1055", match: "Parent", grounded: true },
  { id: "ALT-007", expected: "T1078.003", predicted: "T1078", match: "Parent", grounded: true },
  { id: "ALT-008", expected: "T1486", predicted: "T1486", match: "Exact", grounded: true },
  { id: "ALT-009", expected: "T1003.001", predicted: "T1003.001", match: "Exact", grounded: true },
  { id: "ALT-010", expected: "T1070.004", predicted: "T1070", match: "Parent", grounded: false },
  { id: "ALT-011", expected: "T1036.005", predicted: "T1036.005", match: "Exact", grounded: true },
  { id: "ALT-012", expected: "T1041", predicted: "T1071.001", match: "Miss", grounded: false },
  { id: "ALT-013", expected: "T1204.002", predicted: "T1204.002", match: "Exact", grounded: true },
  { id: "ALT-014", expected: "T1547.001", predicted: "T1547.001", match: "Exact", grounded: true },
  { id: "ALT-015", expected: "T1027", predicted: "T1027", match: "Exact", grounded: true },
  { id: "BEN-001", expected: "NONE", predicted: "NONE", match: "Exact", grounded: true },
  { id: "BEN-002", expected: "NONE", predicted: "NONE", match: "Exact", grounded: true },
  { id: "BEN-003", expected: "NONE", predicted: "NONE", match: "Exact", grounded: true },
  { id: "BEN-004", expected: "NONE", predicted: "T1072", match: "Miss", grounded: false },
  { id: "BEN-005", expected: "NONE", predicted: "NONE", match: "Exact", grounded: true },
  { id: "AMB-001", expected: "T1059", predicted: "T1059", match: "Exact", grounded: true },
  { id: "AMB-002", expected: "T1055", predicted: "T1059.001", match: "Miss", grounded: true },
];

// ─── Main App ───────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState<0 | 1>(0);

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column", background: "var(--background)", overflow: "hidden" }}>
      {/* Top Bar */}
      <header style={{ borderBottom: "1px solid var(--border)", background: "var(--card)", flexShrink: 0 }}>
        <div style={{ padding: "0 24px", display: "flex", alignItems: "center", gap: 32, height: 52 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 16, color: "var(--primary)" }}>⚔</span>
            <span className="mono" style={{ fontSize: 13, fontWeight: 700, color: "var(--foreground)", letterSpacing: "0.06em" }}>ATT&CK INFERENCE ENGINE</span>
            <span className="mono" style={{ fontSize: 10, color: "var(--muted-foreground)", background: "var(--muted)", padding: "2px 6px", borderRadius: 2, letterSpacing: "0.04em" }}>v2.4.1</span>
          </div>
          <nav style={{ display: "flex", gap: 0, marginLeft: "auto" }}>
            {[
              { label: "Analyst Workspace", idx: 0 },
              { label: "Eval & Guardrails", idx: 1 },
            ].map((t) => (
              <button
                key={t.idx}
                onClick={() => setActiveTab(t.idx as 0 | 1)}
                style={{
                  background: "transparent",
                  border: "none",
                  borderBottom: activeTab === t.idx ? "2px solid var(--primary)" : "2px solid transparent",
                  color: activeTab === t.idx ? "var(--primary)" : "var(--muted-foreground)",
                  padding: "0 20px",
                  height: 52,
                  cursor: "pointer",
                  fontSize: 13,
                  fontWeight: 500,
                  fontFamily: "inherit",
                  letterSpacing: "0.02em",
                  transition: "color 0.15s",
                }}
              >
                {t.label}
              </button>
            ))}
          </nav>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--green)", display: "inline-block" }} />
            <span className="mono" style={{ fontSize: 10, color: "var(--muted-foreground)" }}>MITRE ATT&CK Enterprise v19.1</span>
          </div>
        </div>
      </header>

      {/* Tab Content */}
      <div role="note" style={{ padding: "8px 24px", background: "var(--muted)", color: "var(--primary)", fontSize: 12, flexShrink: 0 }}>
        UI preview — predictions, evaluation scores, and guardrail statuses are sample data, not API results. Expert review is required.
      </div>
      <div style={{ flex: 1, overflow: "hidden" }}>
        {activeTab === 0 ? <AnalystWorkspace /> : <EvalDashboard />}
      </div>
    </div>
  );
}

// ─── Tab 1: Analyst Workspace ───────────────────────────────────────────────
function AnalystWorkspace() {
  const [text, setText] = useState("");
  const [sampleIdx, setSampleIdx] = useState<number | null>(null);
  const [result, setResult] = useState<InferenceResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [entitiesOpen, setEntitiesOpen] = useState(false);
  const [candidatesOpen, setCandidatesOpen] = useState(false);

  function pickSample(idx: number) {
    setSampleIdx(idx);
    setText(SAMPLES[idx].text);
    setResult(null);
    setEntitiesOpen(false);
    setCandidatesOpen(false);
  }

  function runInference() {
    if (!text.trim()) return;
    setLoading(true);
    setResult(null);
    setTimeout(() => {
      const r = sampleIdx !== null ? INFERENCE_RESULTS[sampleIdx] : INFERENCE_RESULTS[0];
      setResult(r);
      setEntitiesOpen(true);
      setLoading(false);
    }, 1400);
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", height: "100%", overflow: "hidden" }}>
      {/* LEFT: Input Panel */}
      <div style={{ borderRight: "1px solid var(--border)", display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Quick Picker */}
        <div style={{ padding: "14px 20px 12px", borderBottom: "1px solid var(--border)", background: "var(--muted)", flexShrink: 0 }}>
          <div className="mono" style={{ fontSize: 10, color: "var(--muted-foreground)", letterSpacing: "0.08em", marginBottom: 10 }}>SAMPLE ALERTS — QUICK PICKER</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {SAMPLES.map((s, i) => (
              <button
                key={i}
                onClick={() => pickSample(i)}
                style={{
                  background: sampleIdx === i ? "var(--primary)" : "var(--secondary)",
                  color: sampleIdx === i ? "var(--primary-foreground)" : "var(--foreground)",
                  border: `1px solid ${sampleIdx === i ? "var(--primary)" : "var(--border)"}`,
                  borderRadius: "var(--radius)",
                  padding: "6px 12px",
                  fontSize: 12,
                  fontWeight: 500,
                  cursor: "pointer",
                  fontFamily: "inherit",
                  transition: "all 0.15s",
                }}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Textarea */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", padding: 20 }}>
          <div className="mono" style={{ fontSize: 10, color: "var(--muted-foreground)", letterSpacing: "0.08em", marginBottom: 8 }}>RAW ALERT / LOG NARRATIVE</div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={"Paste security alert, SIEM log, or incident narrative here...\n\nSupports: Syslog, Windows Event Log, EDR telemetry, SOC narrative reports."}
            style={{
              flex: 1,
              background: "var(--muted)",
              color: "var(--foreground)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              padding: 14,
              resize: "none",
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 12,
              lineHeight: 1.7,
              outline: "none",
              transition: "border-color 0.15s",
            }}
            onFocus={(e) => (e.target.style.borderColor = "rgba(245,158,11,0.4)")}
            onBlur={(e) => (e.target.style.borderColor = "var(--border)")}
          />

          {/* Action Button */}
          <button
            onClick={runInference}
            disabled={loading || !text.trim()}
            style={{
              marginTop: 14,
              background: loading || !text.trim() ? "var(--secondary)" : "var(--primary)",
              color: loading || !text.trim() ? "var(--muted-foreground)" : "var(--primary-foreground)",
              border: "none",
              borderRadius: "var(--radius)",
              padding: "12px 24px",
              fontSize: 14,
              fontWeight: 700,
              cursor: loading || !text.trim() ? "not-allowed" : "pointer",
              fontFamily: "inherit",
              letterSpacing: "0.02em",
              transition: "all 0.15s",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
            }}
          >
            {loading ? (
              <>
                <span style={{ display: "inline-block", animation: "spin 1s linear infinite" }}>⟳</span>
                Inferring ATT&CK Techniques...
              </>
            ) : (
              "🔍  Infer ATT&CK Techniques"
            )}
          </button>
        </div>

        {/* Entities Accordion */}
        {result && (
          <div style={{ borderTop: "1px solid var(--border)", flexShrink: 0 }}>
            <button
              onClick={() => setEntitiesOpen(!entitiesOpen)}
              style={{
                width: "100%",
                background: "var(--muted)",
                border: "none",
                borderBottom: entitiesOpen ? "1px solid var(--border)" : "none",
                color: "var(--foreground)",
                padding: "12px 20px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                cursor: "pointer",
                fontFamily: "inherit",
              }}
            >
              <span className="mono" style={{ fontSize: 10, letterSpacing: "0.08em", color: "var(--muted-foreground)" }}>EXTRACTED ENTITIES</span>
              <span style={{ color: "var(--primary)", fontSize: 12 }}>{entitiesOpen ? "▲" : "▼"}</span>
            </button>
            {entitiesOpen && (
              <div style={{ padding: "16px 20px 20px", background: "var(--muted)", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
                <EntityGroup label="ASSETS" items={result.entities.assets} color="#3b82f6" />
                <EntityGroup label="IOCs" items={result.entities.iocs} color="var(--red)" />
                <EntityGroup label="OBSERVED ACTIONS" items={result.entities.actions} color="var(--orange)" />
              </div>
            )}
          </div>
        )}
      </div>

      {/* RIGHT: Results Panel */}
      <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Advisory Banner */}
        <div style={{ background: "rgba(245,158,11,0.08)", borderBottom: "1px solid rgba(245,158,11,0.2)", padding: "10px 20px", flexShrink: 0, display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 14 }}>⚠</span>
          <div>
            <span style={{ fontSize: 12, color: "#fbbf24", fontWeight: 600 }}>Advisory tagging only. Not autonomous SOC action.</span>
            <span style={{ fontSize: 12, color: "var(--muted-foreground)", marginLeft: 6 }}>Verify with senior analyst. </span>
          </div>
          <span className="mono" style={{ marginLeft: "auto", fontSize: 10, color: "var(--muted-foreground)", whiteSpace: "nowrap" }}>MITRE ATT&CK Enterprise v19.1</span>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: 20 }}>
          {!result && !loading && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 12 }}>
              <span style={{ fontSize: 40, opacity: 0.2 }}>⚔</span>
              <p className="mono" style={{ fontSize: 12, color: "var(--muted-foreground)", textAlign: "center" }}>
                Select a sample or paste an alert,<br />then click Infer ATT&CK Techniques.
              </p>
            </div>
          )}

          {loading && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: 16 }}>
              <span style={{ fontSize: 32, color: "var(--primary)", animation: "spin 1s linear infinite", display: "inline-block" }}>⟳</span>
              <p className="mono" style={{ fontSize: 11, color: "var(--muted-foreground)" }}>Running RAG retrieval + LLM inference...</p>
            </div>
          )}

          {result && !loading && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              {/* Review Flag */}
              <div style={{
                background: result.needsReview ? "rgba(239,68,68,0.08)" : "rgba(34,197,94,0.08)",
                border: `1px solid ${result.needsReview ? "rgba(239,68,68,0.25)" : "rgba(34,197,94,0.25)"}`,
                borderRadius: "var(--radius)",
                padding: "10px 14px",
                display: "flex",
                alignItems: "flex-start",
                gap: 10,
              }}>
                <span style={{ color: result.needsReview ? "var(--red)" : "var(--green)", fontWeight: 700, fontSize: 13 }}>
                  {result.needsReview ? "⚠" : "✓"}
                </span>
                <div>
                  <span className="mono" style={{ fontSize: 10, letterSpacing: "0.06em", color: result.needsReview ? "var(--red)" : "var(--green)", fontWeight: 700 }}>
                    {result.needsReview ? "NEEDS HUMAN REVIEW: TRUE" : "GROUNDING STATUS: CLEAR"}
                  </span>
                  <p style={{ fontSize: 12, color: "var(--card-foreground)", marginTop: 4 }}>{result.reviewReason}</p>
                </div>
              </div>

              {/* Technique Cards */}
              {result.techniques.length === 0 ? (
                <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "24px 20px", textAlign: "center" }}>
                  <span className="mono" style={{ fontSize: 12, color: "var(--muted-foreground)" }}>No malicious techniques inferred. Benign activity pattern.</span>
                </div>
              ) : (
                result.techniques.map((t) => <TechniqueCard key={t.id} technique={t} />)
              )}

              {/* Candidate Drawer */}
              <div style={{ border: "1px solid var(--border)", borderRadius: "var(--radius)", overflow: "hidden" }}>
                <button
                  onClick={() => setCandidatesOpen(!candidatesOpen)}
                  style={{
                    width: "100%",
                    background: "var(--secondary)",
                    border: "none",
                    color: "var(--card-foreground)",
                    padding: "11px 16px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    cursor: "pointer",
                    fontFamily: "inherit",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span className="mono" style={{ fontSize: 10, letterSpacing: "0.08em", color: "var(--muted-foreground)" }}>CANDIDATE RETRIEVAL — RAG TOP-5</span>
                    <span style={{ fontSize: 10, background: "var(--muted)", color: "var(--primary)", padding: "2px 6px", borderRadius: 2, fontFamily: "monospace" }}>TRANSPARENT</span>
                  </div>
                  <span style={{ color: "var(--primary)", fontSize: 11 }}>{candidatesOpen ? "▲ Hide" : "▼ View Candidates Considered"}</span>
                </button>
                {candidatesOpen && (
                  <div style={{ background: "var(--card)", padding: "4px 0" }}>
                    {result.candidates.map((c) => (
                      <div key={c.rank} style={{ display: "grid", gridTemplateColumns: "28px 90px 1fr 60px", alignItems: "center", gap: 12, padding: "8px 16px", borderBottom: "1px solid var(--border)" }}>
                        <span className="mono" style={{ fontSize: 10, color: "var(--muted-foreground)" }}>#{c.rank}</span>
                        <span className="mono" style={{ fontSize: 11, color: "var(--primary)", fontWeight: 600 }}>{c.id}</span>
                        <span style={{ fontSize: 12, color: "var(--card-foreground)" }}>{c.name}</span>
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <div className="progress-bar" style={{ flex: 1 }}>
                            <div className="progress-fill" style={{ width: `${c.score * 100}%`, background: scoreColor(c.score) }} />
                          </div>
                          <span className="mono" style={{ fontSize: 10, color: "var(--muted-foreground)", minWidth: 32 }}>{(c.score * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

function EntityGroup({ label, items, color }: { label: string; items: string[]; color: string }) {
  return (
    <div>
      <div className="mono" style={{ fontSize: 9, letterSpacing: "0.1em", color: "var(--muted-foreground)", marginBottom: 8 }}>{label}</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {items.map((item) => (
          <span key={item} className="mono" style={{ fontSize: 11, color, background: `color-mix(in srgb, ${color} 10%, transparent)`, padding: "3px 8px", borderRadius: 2, display: "inline-block" }}>
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

function TechniqueCard({ technique: t }: { technique: Technique }) {
  return (
    <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)", overflow: "hidden" }}>
      {/* Header */}
      <div style={{ padding: "14px 16px 12px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "flex-start", gap: 12 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
            <span className="mono" style={{ fontSize: 13, fontWeight: 700, color: "var(--primary)" }}>{t.id}</span>
            <span style={{ fontSize: 10, background: t.tacticColor + "25", color: t.tacticColor, padding: "2px 8px", borderRadius: 2, fontWeight: 600, letterSpacing: "0.04em" }}>
              {t.tactic}
            </span>
          </div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "var(--foreground)" }}>{t.name}</div>
        </div>
        <a
          href={t.mitreUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={{ fontSize: 11, color: "var(--primary)", border: "1px solid rgba(245,158,11,0.3)", padding: "4px 10px", borderRadius: 2, textDecoration: "none", whiteSpace: "nowrap", fontWeight: 500 }}
        >
          MITRE ↗
        </a>
      </div>

      {/* Confidence */}
      <div style={{ padding: "10px 16px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 12 }}>
        <span className="mono" style={{ fontSize: 10, color: "var(--muted-foreground)", minWidth: 120 }}>CONFIDENCE</span>
        <div className="progress-bar" style={{ flex: 1 }}>
          <div className="progress-fill" style={{ width: `${t.confidence}%`, background: scoreColor(t.confidence / 100) }} />
        </div>
        <span className="mono" style={{ fontSize: 12, fontWeight: 700, color: scoreColor(t.confidence / 100), minWidth: 40, textAlign: "right" }}>{t.confidence}%</span>
      </div>

      {/* Evidence Spans */}
      <div style={{ padding: "12px 16px" }}>
        <div className="mono" style={{ fontSize: 9, letterSpacing: "0.1em", color: "var(--muted-foreground)", marginBottom: 8 }}>EVIDENCE SPANS (GROUNDED)</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {t.evidence.map((e, i) => (
            <div key={i} style={{ background: "rgba(245,158,11,0.07)", borderLeft: "2px solid var(--primary)", padding: "6px 10px", borderRadius: "0 2px 2px 0" }}>
              <span className="mono" style={{ fontSize: 11, color: "#fde68a", lineHeight: 1.5 }}>"{e}"</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function scoreColor(score: number) {
  if (score >= 0.8) return "var(--green)";
  if (score >= 0.5) return "var(--orange)";
  return "var(--red)";
}

// ─── Tab 2: Eval & Guardrails Dashboard ────────────────────────────────────
function EvalDashboard() {
  const [running, setRunning] = useState(false);
  const [runComplete, setRunComplete] = useState(false);
  const [filter, setFilter] = useState<"All" | "Exact" | "Parent" | "Miss">("All");

  function runEval() {
    setRunning(true);
    setRunComplete(false);
    setTimeout(() => {
      setRunning(false);
      setRunComplete(true);
    }, 2800);
  }

  const metrics = [
    { label: "Exact Technique F1", value: 78, target: 70, unit: "%", desc: "F1 score on exact sub-technique match" },
    { label: "Parent Technique Recall", value: 93, target: 90, unit: "%", desc: "Recall when matching at parent level" },
    { label: "Evidence Grounding Rate", value: 88, target: 85, unit: "%", desc: "Predictions with valid evidence spans" },
    { label: "Hallucinated ID Rate", value: 0, target: 0, unit: "%", desc: "Fabricated technique IDs not in ATT&CK", lowerIsBetter: true },
  ];

  const filteredRows = EVAL_ROWS.filter((r) => filter === "All" || r.match === filter);

  return (
    <div style={{ overflowY: "auto", height: "100%", padding: 24 }}>
      {/* Scorecards */}
      <div style={{ marginBottom: 24 }}>
        <SectionLabel>METRIC SCORECARDS — TEST SET (35 MALICIOUS + 10 AMBIGUOUS + 5 BENIGN)</SectionLabel>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginTop: 12 }}>
          {metrics.map((m) => {
            const pass = m.lowerIsBetter ? m.value <= m.target : m.value >= m.target;
            return (
              <div key={m.label} style={{ background: "var(--card)", border: `1px solid ${pass ? "rgba(34,197,94,0.2)" : "rgba(239,68,68,0.2)"}`, borderRadius: "var(--radius)", padding: "20px 20px 18px" }}>
                <div className="mono" style={{ fontSize: 9, letterSpacing: "0.1em", color: "var(--muted-foreground)", marginBottom: 12 }}>{m.label.toUpperCase()}</div>
                <div style={{ display: "flex", alignItems: "flex-end", gap: 4, marginBottom: 10 }}>
                  <span style={{ fontSize: 40, fontWeight: 700, lineHeight: 1, color: pass ? "var(--green)" : "var(--red)", fontFamily: "'JetBrains Mono', monospace" }}>{m.value}</span>
                  <span className="mono" style={{ fontSize: 18, color: pass ? "var(--green)" : "var(--red)", marginBottom: 4 }}>{m.unit}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
                  <span style={{ fontSize: 11, color: pass ? "var(--green)" : "var(--red)", fontWeight: 600 }}>{pass ? "✓ PASS" : "✗ FAIL"}</span>
                  <span className="mono" style={{ fontSize: 10, color: "var(--muted-foreground)" }}>Target: {m.lowerIsBetter ? "≤" : "≥"}{m.target}{m.unit}</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${Math.min(m.value, 100)}%`, background: pass ? "var(--green)" : "var(--red)" }} />
                </div>
                <div style={{ fontSize: 11, color: "var(--muted-foreground)", marginTop: 8 }}>{m.desc}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Test Run Table */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
          <SectionLabel>TEST RUN BREAKDOWN — {EVAL_ROWS.length} CASES</SectionLabel>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {/* Filter buttons */}
            {(["All", "Exact", "Parent", "Miss"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                style={{
                  background: filter === f ? "var(--secondary)" : "transparent",
                  border: `1px solid ${filter === f ? "var(--primary)" : "var(--border)"}`,
                  color: filter === f ? "var(--primary)" : "var(--muted-foreground)",
                  padding: "4px 12px",
                  borderRadius: "var(--radius)",
                  cursor: "pointer",
                  fontSize: 11,
                  fontFamily: "inherit",
                  transition: "all 0.15s",
                }}
              >
                {f}
              </button>
            ))}
            <button
              onClick={runEval}
              disabled={running}
              style={{
                background: running ? "var(--secondary)" : "var(--primary)",
                color: running ? "var(--muted-foreground)" : "var(--primary-foreground)",
                border: "none",
                borderRadius: "var(--radius)",
                padding: "7px 16px",
                fontSize: 12,
                fontWeight: 700,
                cursor: running ? "not-allowed" : "pointer",
                fontFamily: "inherit",
                display: "flex",
                alignItems: "center",
                gap: 6,
                marginLeft: 8,
              }}
            >
              {running ? (
                <><span style={{ display: "inline-block", animation: "spin 1s linear infinite" }}>⟳</span> Running...</>
              ) : (
                "▶  Run Full Evaluation"
              )}
            </button>
          </div>
        </div>

        {runComplete && (
          <div style={{ background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.25)", borderRadius: "var(--radius)", padding: "8px 14px", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ color: "var(--green)", fontWeight: 700 }}>✓</span>
            <span className="mono" style={{ fontSize: 11, color: "var(--green)" }}>Evaluation complete — {EVAL_ROWS.length} test cases processed. Results updated.</span>
          </div>
        )}

        <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: "var(--radius)", overflow: "hidden" }}>
          <div style={{ display: "grid", gridTemplateColumns: "90px 1fr 1fr 100px 130px", background: "var(--secondary)", padding: "9px 16px", gap: 12 }}>
            {["Alert ID", "Expected (Gold)", "Predicted", "Match Type", "Grounding Status"].map((h) => (
              <span key={h} className="mono" style={{ fontSize: 9, letterSpacing: "0.08em", color: "var(--muted-foreground)" }}>{h}</span>
            ))}
          </div>
          <div style={{ maxHeight: 340, overflowY: "auto" }}>
            {filteredRows.map((row, i) => (
              <div
                key={row.id}
                style={{
                  display: "grid",
                  gridTemplateColumns: "90px 1fr 1fr 100px 130px",
                  padding: "8px 16px",
                  gap: 12,
                  borderBottom: "1px solid var(--border)",
                  background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.015)",
                  alignItems: "center",
                }}
              >
                <span className="mono" style={{ fontSize: 11, color: "var(--muted-foreground)" }}>{row.id}</span>
                <span className="mono" style={{ fontSize: 11, color: "var(--card-foreground)" }}>{row.expected}</span>
                <span className="mono" style={{ fontSize: 11, color: row.predicted === row.expected ? "var(--green)" : row.match === "Parent" ? "var(--orange)" : "var(--red)" }}>{row.predicted}</span>
                <MatchBadge match={row.match} />
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: row.grounded ? "var(--green)" : "var(--red)", flexShrink: 0 }} />
                  <span className="mono" style={{ fontSize: 10, color: row.grounded ? "var(--green)" : "var(--red)" }}>{row.grounded ? "Grounded" : "Ungrounded"}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Guardrails */}
      <div>
        <SectionLabel>SECURITY GUARDRAILS STATUS</SectionLabel>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginTop: 12 }}>
          <GuardrailCard
            title="Prompt Injection Testing"
            status="PASS"
            detail="Tested against 10 adversarial log payloads"
            metrics={[
              { label: "Prompt Leakage", value: 0, target: 0 },
              { label: "Taxonomical Escape", value: 0, target: 0 },
              { label: "Role Confusion Attempts Blocked", value: 10, target: 10 },
            ]}
          />
          <GuardrailCard
            title="Hallucination Containment"
            status="PASS"
            detail="All inferred IDs validated against ATT&CK v19.1 taxonomy"
            metrics={[
              { label: "Fabricated Technique IDs", value: 0, target: 0 },
              { label: "Out-of-taxonomy References", value: 0, target: 0 },
              { label: "Confidence Calibration Drift", value: 0.02, target: 0.05, decimals: 2, label2: "MAE" },
            ]}
          />
          <GuardrailCard
            title="Scope Containment"
            status="PASS"
            detail="System enforces advisory-only mode; no autonomous actions executed"
            metrics={[
              { label: "Autonomous Action Attempts", value: 0, target: 0 },
              { label: "SOC Workflow Bypasses", value: 0, target: 0 },
              { label: "Privilege Escalation Attempts", value: 0, target: 0 },
            ]}
          />
          <GuardrailCard
            title="Data Leakage Prevention"
            status="PASS"
            detail="System prompt, retrieval index, and model weights not exposed in any output"
            metrics={[
              { label: "System Prompt Leaks", value: 0, target: 0 },
              { label: "Index Content Leaks", value: 0, target: 0 },
              { label: "PII Exposure Events", value: 0, target: 0 },
            ]}
          />
        </div>
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <div className="mono" style={{ fontSize: 10, letterSpacing: "0.1em", color: "var(--muted-foreground)" }}>{children}</div>;
}

function MatchBadge({ match }: { match: string }) {
  const colors: Record<string, string> = { Exact: "var(--green)", Parent: "var(--orange)", Miss: "var(--red)" };
  const color = colors[match] || "var(--muted-foreground)";
  return (
    <span className="mono" style={{ fontSize: 10, color, background: `color-mix(in srgb, ${color} 10%, transparent)`, padding: "2px 8px", borderRadius: 2, fontWeight: 600, letterSpacing: "0.04em", display: "inline-block" }}>
      {match.toUpperCase()}
    </span>
  );
}

function GuardrailCard({ title, status, detail, metrics }: {
  title: string;
  status: string;
  detail: string;
  metrics: { label: string; value: number; target: number; decimals?: number; label2?: string }[];
}) {
  const pass = status === "PASS";
  return (
    <div style={{ background: "var(--card)", border: `1px solid ${pass ? "rgba(34,197,94,0.2)" : "rgba(239,68,68,0.2)"}`, borderRadius: "var(--radius)", padding: "18px 20px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: "var(--foreground)" }}>{title}</span>
        <span style={{ fontSize: 11, fontWeight: 700, color: pass ? "var(--green)" : "var(--red)", background: pass ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)", padding: "2px 10px", borderRadius: 2 }}>
          {pass ? "✓ " : "✗ "}{status}
        </span>
      </div>
      <p style={{ fontSize: 12, color: "var(--muted-foreground)", marginBottom: 14 }}>{detail}</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {metrics.map((m) => {
          const ok = m.value <= m.target;
          return (
            <div key={m.label} style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: 11, color: "var(--card-foreground)" }}>{m.label}</span>
              <span className="mono" style={{ fontSize: 12, fontWeight: 700, color: ok ? "var(--green)" : "var(--red)" }}>
                {m.decimals ? m.value.toFixed(m.decimals) : m.value} {m.label2 || ""}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
