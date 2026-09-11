# v0.2.0 runtime evaluation report

## Reproduction contract

This checked-in release asset records the offline runtime evaluation for the
fixed 10-alert `iteration_2_v0.2.0` subset. It is produced from the pinned
MITRE ATT&CK Enterprise STIX 2.1 `enterprise-attack-19.1` knowledge base after:

```bash
python -m src.rag.ingest_stix
GOOGLE_API_KEY='' GEMINI_API_KEY='' python -m eval.run_eval --mode runtime --subset iteration-2
```

The runner calls the real local pipeline with `use_provider=False`; it makes no
network/provider call even if keys are present. The report uses BM25 top-k 5,
router-dispatched tactic specialists, the lexical offline inferencer, parent-match
credit 0.5, and exact-substring evidence grounding. Dataset labels are `1.0.0-rc1` and
`pending_independent_review`.

## Result

| Metric | Runtime result |
| --- | ---: |
| Alerts evaluated | 10 |
| Exact precision | 27.78% |
| Exact recall | 45.45% |
| Exact F1 | 34.48% |
| Parent technique recall | 50.00% |
| Evidence grounding rate (substring) | 100.00% |
| Hallucinated ID rate | 0.00% |
| False-positive rate | 50.00% |
| Human-review rate | 30.00% |
| Recall@1 / Recall@3 / Recall@5 | 27.27% / 63.64% / 63.64% |

The run passed the Iteration 2 execution requirement (the pipeline and metrics
completed), but did not pass the final-demo quality gates: F1 is below 70% and
parent recall below 90%. A successful evaluation run does not assert those
final thresholds.
