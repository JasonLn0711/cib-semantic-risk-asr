# Counterfactual Variant Contract

CDS-ASR generates plausible transcript alternatives around risk atoms, then
tests whether those alternatives change the downstream decision.

## Variant Sources

Use three sources together:

1. Acoustic ambiguity:
   - ASR confidence;
   - token log probability;
   - n-best hypotheses;
   - timestamp-aligned unstable spans.
2. Mandarin phonetic confusion:
   - homophones;
   - near-homophones;
   - tone-sensitive pairs;
   - number-unit confusion such as `三萬` / `三十萬`;
   - short function words such as negation markers.
3. Fraud-domain slot ontology:
   - amount;
   - payment action;
   - caller identity;
   - account state;
   - time;
   - intent;
   - scam pattern.

## Required TSV Columns

Use `sample_counterfactual_variants.tsv` as the minimum schema.

| Column | Meaning |
| --- | --- |
| `sample_id` | Segment identifier. |
| `variant_id` | Unique variant id within sample. |
| `base_decision` | Decision from top-1 ASR transcript. |
| `variant_decision` | Decision from the counterfactual transcript. |
| `acoustic_plausibility` | `0-1` plausibility of the variant from audio evidence. |
| `risk_atom_type` | Atom type from `../taxonomy/decision_critical_error_taxonomy.yaml`. |
| `risk_atom_weight` | Optional explicit weight; default comes from scoring script. |
| `decision_distance` | Optional explicit distance; default comes from label order. |
| `base_transcript` | Top-1 transcript or safe redacted sample. |
| `variant_transcript` | Plausible transcript alternative or safe redacted sample. |
| `note` | Why this variant matters. |

## Decision Label Order

Default escalation order:

```text
no_escalation < review < priority_review < critical_escalation
```

The default decision distance is the absolute difference in this order.

## Safety Rule

Do not commit raw call transcripts unless they are synthetic, redacted, or
explicitly cleared for publication. For real data, store aggregate CEIS outputs
and safe examples only.
