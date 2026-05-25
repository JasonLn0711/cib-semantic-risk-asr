# Run Record: janus_300_high_stakes_metric_predictor_proxy_2026_05_25

## Summary

- Status: proxy completed
- Date: 2026-05-25
- Dataset: JANUS selected 300 high-stakes expansion
- Inputs: three-model selected-300 SRES/CEIS/downstream proxy outputs
- Model-samples: `900`
- Output boundary: aggregate-only; no transcripts or sample IDs are tracked

## Purpose

Test whether ordinary ASR surface metrics explain downstream CDS risk. This is
the paper-facing bridge between the WER audit and the CDS-ASR claim: WER/CER
must be reported correctly, but in high-stakes decision systems they are not
enough to decide whether an ASR output is safe.

## Command

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/analyze_metric_predictors.py \
  --sres-scored 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/sres_scored.tsv \
  --ceis-scored 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/ceis_scored.tsv \
  --downstream-decisions 70_experiments/runs/janus_300_high_stakes_cds_proxy_2026_05_25/artifacts/metric_inputs_three_model/downstream_escalation_decisions.tsv \
  --output-dir 70_experiments/runs/janus_300_high_stakes_metric_predictor_proxy_2026_05_25
```

Runtime: `0.2486` seconds.

## Output Files

| File | Content |
| --- | --- |
| `metric_predictor_summary.json` | Aggregate summary, thresholds, per-run counts, and best overall predictors. |
| `metric_predictor_comparison.tsv` | AUC and descriptive best-threshold F1 for each metric/target pair. |
| `risk_atom_instability.tsv` | Risk-atom instability counts by ASR run and atom type. |
| `low_wer_danger_summary.tsv` | Aggregate count of low-WER rows that still carry downstream/risk signals. |

## Aggregate Predictor Results

Overall selected targets:

| Target | Metric | AUC | Best F1 | Precision | Recall |
| --- | --- | ---: | ---: | ---: | ---: |
| Unsafe downrouting | WER | `0.7683` | `0.2892` | `0.2222` | `0.4138` |
| Unsafe downrouting | CER | `0.7739` | `0.2373` | `0.2333` | `0.2414` |
| Unsafe downrouting | SRES total | `0.9954` | `0.9062` | `0.8286` | `1.0000` |
| Unsafe downrouting | CEIS max | `0.9971` | `0.9062` | `0.8286` | `1.0000` |
| High-risk missed | WER | `0.6871` | `0.2500` | `0.2000` | `0.3333` |
| High-risk missed | CER | `0.7138` | `0.2500` | `0.5000` | `0.1667` |
| High-risk missed | SRES total | `0.9826` | `0.2927` | `0.1714` | `1.0000` |
| High-risk missed | CEIS max | `0.9973` | `0.9091` | `1.0000` | `0.8333` |
| Danger event | WER | `0.7629` | `0.2697` | `0.2222` | `0.3429` |
| Danger event | CER | `0.7676` | `0.2154` | `0.2333` | `0.2000` |
| Danger event | SRES total | `1.0000` | `1.0000` | `1.0000` | `1.0000` |
| Danger event | CEIS max | `1.0000` | `1.0000` | `1.0000` | `1.0000` |

Interpretation: correctly segmented WER and CER are still useful ASR quality
signals, but they are weak predictors of downstream safety compared with
risk-aware proxy signals on this selected-300 slice. Because SRES/CEIS are
derived from proxy risk rows in this run, the result is engineering evidence
and must be human-audited before becoming a formal paper claim.

## Per-Run Risk Counts

| Run | Rows | Mean WER | Mean CER | Label flips | Unsafe downrouting | High-risk missed | Critical miss |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `breeze_asr25_partial_encoder_high_stakes_300` | 300 | `9.5535` | `7.0345` | 4 | 3 | 1 | 0 |
| `breeze_asr25_lora_high_stakes_300` | 300 | `22.1503` | `16.1523` | 9 | 6 | 0 | 0 |
| `breeze_asr25_base_high_stakes_300` | 300 | `28.7416` | `22.0653` | 22 | 20 | 5 | 1 |

## Low-WER Danger Check

Low WER threshold: `10.0`.

| Run | Low-WER rows | Low-WER label flips | Low-WER unsafe downrouting | Low-WER high-risk missed | Low-WER any danger |
| --- | ---: | ---: | ---: | ---: | ---: |
| ALL | 237 | 2 | 2 | 0 | 2 |
| `breeze_asr25_partial_encoder_high_stakes_300` | 192 | 1 | 1 | 0 | 1 |
| `breeze_asr25_lora_high_stakes_300` | 36 | 0 | 0 | 0 | 0 |
| `breeze_asr25_base_high_stakes_300` | 9 | 1 | 1 | 0 | 1 |

This supports the claim that low WER is not equivalent to downstream safety,
even after fixing the Chinese WER calculation policy.

## Risk-Atom Instability Signal

Highest unstable-variant rates by model:

| Run | Highest atom | Unstable variant rate | Affected samples |
| --- | --- | ---: | ---: |
| `breeze_asr25_base_high_stakes_300` | negation | `0.0942` | 13 |
| `breeze_asr25_lora_high_stakes_300` | amount | `0.0374` | 8 |
| `breeze_asr25_partial_encoder_high_stakes_300` | actor | `0.0171` | 4 |

## Boundary And Next Gate

This run does not replace human review. The next paper-grade gate is a
selected-300 human risk-atom audit with repo-safe aggregate annotation stats.
Only after that audit should SRES/CEIS predictor numbers be described as
reviewed evidence rather than proxy evidence.
