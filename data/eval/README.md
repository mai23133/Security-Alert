# Offline evaluation dataset

This directory belongs to stream C (dataset and evaluation) and contains no real
alert data. All narratives are synthetic and sanitized.

## Files and schema

- `alerts-v1.0.json`: 35 gold examples. Each item has `alert_id`, `narrative`,
  `category`, and `gold_technique_ids`.
- `saved_predictions-v1.0.json`: deterministic provider-free predictions and
  ranked candidates used to test every metric.
- `technique_ids-v19.1.json`: an evaluation snapshot of the Windows/Linux IDs in
  the three in-scope tactics from pinned Enterprise ATT&CK 19.1. It is not a new
  taxonomy source; `data/raw/enterprise-attack-19.1.json` remains authoritative.

Categories contain 20 single-label positives, 5 multi-technique examples, 5
ambiguous examples, and 5 negative controls. Ambiguous examples may still have a
reviewed expected label but are expected to set `needs_human_review`.

## Reproduction

Run from the repository root:

```powershell
python -m eval.run_eval
python -m eval.run_eval --output data/eval/report-v1.0.json
```

The saved fixture records `model_version=synthetic-saved-predictions` and
`prompt_version=none`; it never contacts Gemini or the network.

The generated report is a `fixture_validation` report with
`not_a_runtime_quality_gate=true`. Its perfect prediction scores verify the
metric and runner implementation only; they do not measure the quality of the
real `/alerts/infer` pipeline. A runtime quality report must be generated
separately and record its model, prompt, dataset, and STIX versions.

Parent technique recall awards `1.0` for an exact technique match and `0.5` for
predicting only the parent of a gold sub-technique. All other matches receive
zero credit.

## Version and label review

- Dataset version: `1.0.0-rc1`
- STIX version: `enterprise-attack-19.1`
- Authoring status: complete (35/35 records)
- Independent gold-label review: **pending**

The dataset must remain an RC and must not be declared locked `1.0.0` until a
second team member records their name/date in the dataset metadata after checking
every gold ID and narrative mapping.
