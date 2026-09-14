# Development fixtures

`alerts.json` contains synthetic cases authored from the pinned STIX behavior
definitions. It is separate from `data/eval/alerts-v1.0.json` and is not course
gold, a blind holdout, an instructor review, or independent semantic validation.

Run:

```bash
python -m eval.run_eval --mode runtime --development --diagnostics --require-quality-gates
```

The report includes Recall@1/3/5, error taxonomy and confidence bins. The 0.80
review threshold separates explicit behavior scores (0.82) from ambiguous
support (0.60) and exact-name fallback (0.55). These are ordinal rule scores,
not calibrated probabilities. Development precision alone cannot establish
calibration on unseen data; an independently reviewed calibration set is still
required for that claim.

Rules were expanded against STIX concepts and new development cases after
examining error categories/IDs at evaluation checkpoints. Course narratives
were not used as literal rules. Since checkpoint results informed which
behavior classes to improve, the existing course pack is not a fresh blind
holdout; a new independently reviewed holdout is recommended for final claims.
