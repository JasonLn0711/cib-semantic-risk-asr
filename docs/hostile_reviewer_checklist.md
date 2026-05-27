# Hostile Reviewer Checklist

Date: 2026-05-26

Scope: final CDS-ASR submission pass

Use this checklist after manuscript, figures, citations, claim registry, and
artifact package are updated. The goal is not to reopen evidence collection;
the goal is to verify that every claim is scoped, reconstructable, and
privacy-preserving.

| Check | Required answer |
| --- | --- |
| 90 assessments independent? | No. They are 90 model assessments clustered within 30 reviewed audio rows. Row-clustered CI and leave-one-row-out sensitivity are reported. |
| selected-300 selection bias? | Disclosed as an enriched high-stakes audit surface, not prevalence evidence. |
| threshold leakage? | Table 3 thresholds are retrospective diagnostic thresholds, not deployment thresholds. |
| CEIS vs SRES? | CEIS has strongest point AUC and zero-FN diagnostic operating point; SRES has highest best-threshold F1 and fewer false positives. |
| Table 4 CEIS/SRES tie? | Explicitly stated: SRES-triggered and CEIS-triggered conservative policies tie on severe-miss elimination and budget. |
| recovery causal language? | Use aggregate policy replay language, not live deployed causal intervention language. |
| residual unsafe downrouting? | Residual unsafe downrouting remains 24 after SRES/CEIS conservative replay and is discussed as separate governance. |
| confidence-only baseline? | Named calibrated-confidence unavailable; it does not act as a calibrated confidence baseline. |
| CEIS reconstructable? | `docs/ceis_method_spec.md`, `docs/risk_atom_weights.tsv`, `docs/downstream_decision_contract.md`, and `80_semantic_risk_asr/scoring/ceis_config.json` define the method contract. |
| plausibility term? | Written as `Plausibility(v | x)`, a bounded proxy, not an acoustic posterior. |
| variant coverage? | Aggregate CEIS top-atom proxy coverage is reported without variant text; unavailable phonetic/domain/runtime/rejected-variant logs are named as a scope limitation. |
| fixed-budget frontier? | Fixed-budget replay reports the trigger-budget tradeoff separately from diagnostic Table 4 thresholds. |
| N ladder clear? | Manuscript and F6 separate 258 split, selected-300 provenance, 30 reviewed rows, and 90 model assessments. |
| privacy boundary clear? | `docs/privacy_boundary.md` and `docs/artifact_privacy_classes.tsv` define release and local-only boundaries. |
| intended use restricted? | `docs/intended_use_statement.md` disallows adverse automation and direct punitive use. |
| artifact checksums? | Paper and postdoc artifact manifests include SHA256 and source commit metadata. |
| citations complete? | Manuscript citation keys resolve in `references.bib` and official web citations include 2026-05-26 access dates. |
| candidate lane separated? | Candidate models remain in fixed 15-row/runtime gate lane until locale/runtime promotion. |
| locale gate contradiction? | Completed baselines with disclosed violations are retained only as baselines; new promotion requires strict locale gate. |

## Freeze Rule

After the submission-candidate tag, do not add models, full-split runs, or new
evidence boundaries. Only repair wording, citations, tables, figures, appendix
material, and aggregate artifact packaging.
