export interface EvaluationReport {
  metadata: {
    report_kind: string;
    dataset_version: string;
    model_version: string;
    stix_version: string;
    generated_at: string;
    label_review_status: string;
    provider_mode: string;
    category_counts: Record<string, number>;
  };
  metrics: {
    alert_count: number;
    exact_technique: { precision: number; recall: number; f1: number };
    parent_technique_recall: number;
    evidence_grounding_rate: number;
    hallucinated_id_rate: number;
    false_positive_rate: number;
    human_review_rate: number;
  };
  quality_gates: Record<string, boolean>;
  numeric_gates_passed: boolean;
  acceptance_ready: boolean;
  acceptance_blockers: string[];
  disclaimer: string;
  case_results: {
    alert_id: string;
    category: string;
    gold_technique_ids: string[];
    predicted_technique_ids: string[];
    match: 'Exact' | 'Parent' | 'Miss';
    grounded: boolean | null;
    needs_human_review: boolean;
    out_of_subset_ids: string[];
  }[];
}

const isObject = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value);
const isStrings = (value: unknown) => Array.isArray(value) && value.every(item => typeof item === 'string');
const isRate = (value: unknown) => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1;

function isReport(value: unknown): value is EvaluationReport {
  if (!isObject(value) || !isObject(value.metadata) || !isObject(value.metrics) || !isObject(value.quality_gates)) return false;
  const { metadata, metrics, quality_gates } = value;
  if (!['report_kind', 'dataset_version', 'model_version', 'stix_version', 'generated_at', 'label_review_status', 'provider_mode'].every(key => typeof metadata[key] === 'string')) return false;
  if (metadata.report_kind !== 'runtime_quality' || metadata.provider_mode !== 'disabled') return false;
  if (!isObject(metadata.category_counts) || !Object.values(metadata.category_counts).every(n => typeof n === 'number' && Number.isInteger(n) && n >= 0)) return false;
  if (!isObject(metrics.exact_technique) || !['precision', 'recall', 'f1'].every(key => isRate((metrics.exact_technique as Record<string, unknown>)[key]))) return false;
  if (!['parent_technique_recall', 'evidence_grounding_rate', 'hallucinated_id_rate', 'false_positive_rate', 'human_review_rate'].every(key => isRate(metrics[key]))) return false;
  if (!['exact_f1_at_least_0_70', 'parent_recall_at_least_0_90', 'grounding_at_least_0_85', 'hallucinated_id_rate_is_zero'].every(key => typeof quality_gates[key] === 'boolean')) return false;
  if (typeof value.numeric_gates_passed !== 'boolean' || typeof value.acceptance_ready !== 'boolean' || !isStrings(value.acceptance_blockers) || typeof value.disclaimer !== 'string') return false;
  if (!Array.isArray(value.case_results) || value.case_results.length !== metrics.alert_count) return false;
  return value.case_results.every(row => isObject(row) && typeof row.alert_id === 'string' && typeof row.category === 'string'
    && isStrings(row.gold_technique_ids) && isStrings(row.predicted_technique_ids) && isStrings(row.out_of_subset_ids)
    && ['Exact', 'Parent', 'Miss'].includes(String(row.match)) && (row.grounded === null || typeof row.grounded === 'boolean') && typeof row.needs_human_review === 'boolean');
}

export async function runEvaluation(signal: AbortSignal): Promise<EvaluationReport> {
  if (window.location.protocol === 'file:') throw new Error('เปิดหน้า UI ผ่าน http://127.0.0.1:8000/ui เพื่อเชื่อมต่อระบบ');
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort();
  signal.addEventListener('abort', abort, { once: true });
  if (signal.aborted) controller.abort();
  const timer = window.setTimeout(() => { timedOut = true; controller.abort(); }, 120_000);
  let requestId = '';
  try {
    const response = await fetch('/evaluate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: 'runtime', top_k: 5 }), signal: controller.signal,
    });
    requestId = response.headers.get('X-Request-ID') || '';
    const data: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = isObject(data) ? data.detail : null;
      throw new Error(isObject(detail) && typeof detail.message === 'string' ? detail.message : `ประเมินผลไม่สำเร็จ (HTTP ${response.status})`);
    }
    if (!isReport(data)) throw new Error('รายงานไม่ครบหรือรูปแบบไม่ถูกต้อง กรุณาอัปเดตหรือรีสตาร์ต backend แล้วลองใหม่');
    return data;
  } catch (error) {
    if (signal.aborted) throw error;
    const message = timedOut ? 'หมดเวลารอผลประเมิน กรุณาลองใหม่' : error instanceof TypeError ? 'เชื่อมต่อระบบไม่ได้ กรุณาตรวจว่า backend เปิดอยู่'
      : error instanceof Error ? error.message : 'ประเมินผลไม่สำเร็จ';
    throw new Error(requestId ? `${message} · Request ID: ${requestId}` : message);
  } finally {
    window.clearTimeout(timer);
    signal.removeEventListener('abort', abort);
  }
}
