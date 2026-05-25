# Run Record: janus_300_high_stakes_human_audit_selection_2026_05_25

## Summary

- Status: audit selection created, human review pending
- Date: 2026-05-25
- Dataset: JANUS selected 300 high-stakes expansion
- Input: three-model selected-300 SRES/CEIS/downstream proxy outputs
- Candidate audio rows: `300`
- Selected human-audit audio rows: `30`
- Selected model-samples: `90`
- Local review sheet: ignored under `artifacts/human_risk_atom_audit_sheet.tsv`

## Purpose

Create the reviewer-facing human risk-atom audit gate needed before proxy
SRES/CEIS predictor and recovery results can be treated as paper-grade
evidence. The selector intentionally keeps audio IDs, transcripts, and model
hypotheses out of tracked files.

## Command

```bash
.venv/bin/python 80_semantic_risk_asr/annotation/select_human_risk_atom_audit.py \
  --sres-scored 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/sres_scored.tsv \
  --ceis-scored 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/ceis_scored.tsv \
  --downstream-decisions 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/downstream_escalation_decisions.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25 \
  --audit-size 30
```

Runtime: `0.0393` seconds.

## Aggregate Selection Results

| Item | Value |
| --- | ---: |
| Candidate audio rows | 300 |
| Selected audio rows | 30 |
| Selected model-samples | 90 |
| Selected critical-miss audio rows | 1 |
| Selected high-risk-missed audio rows | 6 |
| Selected unsafe-downrouting audio rows | 22 |
| Selected label-flip audio rows | 25 |
| Selected low-WER danger audio rows | 2 |
| Selected high proxy-risk audio rows | 25 |
| Selected model-disagreement audio rows | 22 |

Primary selection strata:

| Stratum | Target quota | Available audio | Primary selected | Selected carrying signal |
| --- | ---: | ---: | ---: | ---: |
| Critical or high-risk missed | 6 | 6 | 6 | 6 |
| Unsafe downrouting | 6 | 22 | 6 | 22 |
| Low-WER danger | 4 | 2 | 0 | 2 |
| High proxy risk | 6 | 25 | 6 | 25 |
| Model disagreement | 4 | 22 | 4 | 22 |
| Clean control | 4 | 275 | 4 | 5 |
| Risk-score fill | - | - | 4 | - |

`Primary selected` is the stratum that claimed the row first. `Selected
carrying signal` counts overlap; for example, the two low-WER danger rows were
already selected by earlier higher-priority strata.

Risk-atom coverage:

| Risk atom | Available audio | Selected audio |
| --- | ---: | ---: |
| action | 25 | 25 |
| actor | 15 | 15 |
| amount | 23 | 23 |
| negation | 14 | 14 |
| scam_pattern | 23 | 23 |

## Local-Only Human Review Sheet

The local ignored sheet contains:

- audio ID;
- split;
- reference transcript;
- per-model hypotheses and metrics;
- current proxy risk signals;
- blank reviewer fields for verified transcript, semantic-risk label, risk
  atoms, critical atoms, decision-change reason, expected safe action,
  confidence, and notes.

The tracked protocol is:
`80_semantic_risk_asr/annotation/selected_300_human_risk_atom_audit_protocol_2026_05_25.md`.

## Boundary

This run does not complete the human audit. It creates the audit queue and
aggregate selection evidence. Paper-facing SRES/CEIS and recovery claims remain
proxy-only until the local sheet is reviewed and aggregate human annotation
statistics are recorded.
