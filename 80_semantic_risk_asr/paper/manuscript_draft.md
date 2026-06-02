# Manuscript Draft

Working title: When Low WER Becomes Dangerous: Counterfactual
Decision-Stability ASR for High-Stakes Speech-Driven Decision Systems

Status: paper-facing v0 draft with second-reviewer evidence-boundary revisions,
results table package, reproducibility layer, scope control, limitations, and
artifact availability plan.

Date: 2026-05-28

## Evidence Boundary Freeze

This manuscript uses a scoped evidence chain:

1. The 258-row test split is used as scope-controlled split and model-comparison
   evidence.
2. The selected-300 proxy outputs are used as input provenance and row-selection
   evidence.
3. The selected-300 human-reviewed predictor and human-reviewed recovery
   outputs are the paper-grade risk and recovery evidence.

Reference transcripts remain accepted human-reviewed ground truth for WER/CER
scoring. Transcript review is not reopened unless a future review task changes
the field scope or challenges the accepted reference transcript content.

Tracked manuscript artifacts must remain aggregate-only. Raw audio, raw
transcripts, audio IDs, selected sample IDs, model hypotheses, local response
sheets, reviewer notes, runtime logs, raw predictions, and model weights remain
local or ignored and are not committed.

Authoritative boundary records:

- `70_experiments/runs/postdoc_evidence_chain_2026_05_25/evidence_chain_readiness_summary.json`
- `70_experiments/runs/postdoc_evidence_chain_2026_05_25/publishable_evidence_completion_summary.json`
- `70_experiments/runs/postdoc_evidence_chain_2026_05_25/consequence_evidence_matrix.tsv`
- `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_refresh_summary.json`

## Abstract

Speech-driven decision systems increasingly transform conversations into
operational signals for routing, escalation, compliance monitoring, and
case-handling decisions. In high-stakes anti-fraud calls, small ASR differences
can land on decision atoms such as negation, amount, actor, action, time, and
intent. A transcript can therefore remain close under WER or CER while a
plausible alternative transcript changes the downstream decision.

We propose Counterfactual Decision-Stability ASR (CDS-ASR), a framework that
evaluates whether downstream decisions remain stable under acoustically and
semantically plausible transcript alternatives. CDS-ASR extracts risk atoms,
constructs plausible ASR alternatives, scores decision instability with
Counterfactual Escalation Instability Score (CEIS), and applies constrained
recovery or conservative machine action for high-risk spans while preserving
aggregate-only reproducibility for sensitive call evidence.

Across a six-model 258-row split comparison, selected-300 high-stakes
provenance outputs, and a completed 300-row dual-reviewer human audit with 900
model-level assessments per reviewer, CDS-ASR provides a consequence-centered
evidence layer beyond transcript similarity. The dual-reviewer audit records
strong agreement for decision-change, semantic-risk, expected-safe-action, and
confidence labels, with Cohen's kappa values of 0.849970, 1.000000, 0.851426,
and 0.934274, respectively. In the current aggregate predictor and
policy-replay surface, CEIS achieves the highest decision-change AUC and a
zero-false-negative operating point, while risk-triggered policies, including
CEIS-triggered conservative action, eliminate high-risk missed and critical
miss counts under the aggregate-only claim boundary. These results support
decision-stability evaluation as a scoped companion to transcript accuracy,
semantic metrics, confidence-aware correction, and reviewer-visible
human-audit reliability.

## Introduction

Speech is no longer only a record of what happened in a call. In modern
contact centers, speech is increasingly converted into operational signals:
categories, summaries, compliance cues, real-time alerts, routing decisions,
and escalation support. Commercial contact-center analytics already describe
voice conversations and transcripts as inputs for automated categorization,
summarization, compliance monitoring, and real-time assistance
[@aws_contact_lens_analytics_2026; @aws_connect_contact_lens_2026]. This turns
ASR output into a decision substrate. A transcript can influence how a case is
categorized, which queue receives it, whether an alert is raised, and whether a
human reviewer ever sees the full call context.

Anti-fraud calls make this speech-to-decision pipeline concrete. Taiwan's
National Police Agency describes the 165 hotline as a public anti-fraud channel
where staff record incident details and provide information to victims
[@npa_165_antifraud_hotline_2024]. The operational scale is large: the FBI's
2025 Internet Crime Report context reported more than one million IC3
complaints and large cyber-enabled fraud losses
[@fbi_crypto_ai_scams_2026; @fbi_ic3_2025_report_2026]. In this setting, the
important spoken facts are often small: whether money was already transferred,
whether the amount was 30,000 or 300,000, who initiated contact, when the event
happened, whether the caller is certain, and whether the scenario matches a
known scam pattern. These are not merely words. They are decision atoms.

This paper starts from the following practical risk: a transcript can be
linguistically close and still operationally unsafe. A single ASR ambiguity
around negation, amount, actor, action, time, intent, or scam pattern can move
a case from routine review to priority review, or from escalation to unsafe
downrouting. In this paper, "dangerous" is operationalized as ASR-induced
decision change that can produce unsafe downrouting, high-risk missed
escalation, or critical miss under the declared anti-fraud triage policy. The
title is therefore a measurable claim about decision consequences, not a
general safety slogan.

Existing ASR evaluation and repair methods provide the foundation for this
problem. WER and CER remain necessary because they make transcript accuracy
auditable and comparable. Semantic ASR metrics make the evidence more
task-aware: Kim et al. motivate Semantic Distance by showing that WER can fail
to reflect downstream spoken-language-understanding behavior, and Rugayan et
al. evaluate Aligned Semantic Distance as a semantic metric that better aligns
with human judgments and downstream tasks
[@kim2021semanticdistance; @rugayan2023asd]. Transcript repair also advances
the pipeline. Naderi et al. study post-hoc ASR correction with LLMs and use
confidence-based filtering to reduce harmful changes to likely accurate
transcripts [@naderi2024llmconfidence]. Selective prediction, reject-option,
and conformal prediction work further show how systems can trade coverage,
abstention, and uncertainty when acting on uncertain predictions is costly
[@chow1970reject; @geifman2017selective; @geifman2019selectivenet;
@angelopoulos2021conformal].

These methods make speech systems more measurable, semantic, correctable, and
uncertainty-aware. The remaining gap is the decision-stability question. A
semantic metric can report that two transcripts are close or far. A correction
model can make a transcript more fluent or more likely. A confidence filter can
avoid some risky changes. Yet a high-stakes workflow also needs to know whether
plausible ASR alternatives would change the downstream action. In anti-fraud
triage, the actionable question is not only "How accurate is the transcript?"
but also: "Would another plausible transcript lead to a different safe action?"

We propose Counterfactual Decision-Stability ASR (CDS-ASR) to answer that
question directly. CDS-ASR extracts decision-critical risk atoms, generates
acoustically and semantically plausible transcript alternatives, measures
decision instability with Counterfactual Escalation Instability Score (CEIS),
and evaluates constrained recovery or conservative machine action for high-risk
spans. WER, CER, semantic metrics, SRES, confidence, and correction baselines
remain comparison layers. The central contribution is the new evaluation view:
ASR for high-stakes speech-driven systems should be judged by whether the
downstream decision remains stable under plausible transcript alternatives.

Verified source anchors for this introduction are maintained in
`citation_seed.md` and `references.bib`, with access dates refreshed on
2026-05-28. Empirical manuscript claims point to the aggregate artifacts listed
in the Appendix.

## Related Work

### Transcript-Centered ASR Metrics

Transcript accuracy metrics provide the reproducible baseline for ASR
comparison. WER and CER remain necessary because they allow stable comparison
across models and splits when tokenization, normalization, micro/macro scope,
and zero-reference handling are declared. This manuscript keeps WER/CER as
auditable surface metrics and uses the repo's metric audit to define the
Chinese ASR reporting policy. The paper does not discard transcript accuracy;
it treats WER/CER as the auditable surface layer that must be reported before
stronger downstream claims are made.

### Semantic And Downstream-Aware ASR Evaluation

Semantic ASR metrics extend transcript evaluation toward meaning preservation
and downstream task behavior. Kim et al. introduce Semantic Distance for ASR
performance analysis toward spoken-language understanding, motivating the move
from literal correctness to semantic correctness for intent recognition, slot
filling, semantic parsing, and named entity recognition
[@kim2021semanticdistance]. Rugayan et al. evaluate Aligned Semantic Distance
against WER and show its value for human perception and downstream NLP tasks
[@rugayan2023asd]. CDS-ASR uses this line of work as a foundation and adds a
direct decision-stability target: whether plausible ASR alternatives change a
high-stakes downstream decision.

### Transcript Repair And Conservative Decision Action

LLM and confidence-aware correction methods provide transcript-repair
baselines. Naderi et al. show that confidence-based filtering can guide
post-hoc LLM correction of ASR transcripts and reduce the chance of changing
likely accurate transcripts [@naderi2024llmconfidence]. CDS-ASR complements
this line by evaluating the decision interval that remains when plausible ASR
alternatives affect risk atoms. Recovery in this manuscript is automatic and
machine-bounded: human review supplies evaluation labels and governance
evidence, while risk-triggered policies supply the scoped intervention test.

The conservative-action layer also connects to selective prediction and
reject-option research. Chow formalizes the error-reject tradeoff for
recognition systems [@chow1970reject], while modern selective classification
and SelectiveNet show how neural systems can abstain or reject to manage
risk-coverage tradeoffs [@geifman2017selective; @geifman2019selectivenet].
Conformal prediction further motivates distribution-free uncertainty sets for
high-risk systems [@angelopoulos2021conformal]. CDS-ASR applies this
governance intuition to speech-driven decision evidence: when transcript
alternatives affect decision atoms, the system should expose the instability or
take conservative action rather than treat one transcript as fully stable.

High-stakes speech domains reinforce the need for consequence-aware ASR
evaluation. In psychotherapy, Miner et al. show that ASR feasibility depends on
the clinical use case and that individual-level safety monitoring requires a
more cautious threshold than population-level language analysis
[@miner2020psychotherapy_asr]. CDS-ASR brings the same claim-evidence
discipline to anti-fraud calls by separating transcript accuracy, semantic
risk, decision instability, and aggregate recovery evidence.

This paper positions ASR models as evidence-producing components. The
protagonist is the downstream decision that changes when an acoustically
plausible transcript difference lands on a decision-critical atom.

## Method

### Problem Formulation

We study speech-driven decision systems where an audio segment is transcribed
by ASR and then used by a downstream escalation workflow. The downstream label
space includes routine review and higher-priority escalation states. The
central unit is a model-sample: one ASR hypothesis for one audio row, evaluated
against aggregate risk and decision-stability evidence.

The paper asks whether the decision remains stable under plausible transcript
alternatives. This makes transcript accuracy a supporting layer and
decision-stability the primary high-stakes safety target.

### CDS-ASR Pipeline

CDS-ASR evaluates high-stakes ASR through a decision-stability pipeline:

```text
audio
-> ASR transcript and runtime/quality signals
-> risk atom extraction
-> plausible counterfactual transcript variants
-> downstream decision model
-> SRES and CEIS scoring
-> constrained recovery or conservative machine action
```

Risk atoms are transcript spans whose alternatives can affect downstream
decisions. This manuscript focuses on negation, amount, action, actor, time,
intent, uncertainty, and scam-pattern atoms.

CEIS scores the maximum decision-flip risk among plausible variants. In this
paper-facing implementation, the plausibility term is a bounded proxy rather
than a calibrated acoustic posterior:

```text
CEIS(x) = max over v in V(x) [
    Plausibility(v | x) * RiskAtomWeight(v) * DecisionDistance(f(x), f(v))
]
```

`Plausibility(v | x)` denotes a bounded proxy plausibility score derived from
model disagreement, Mandarin phonetic ambiguity, domain-slot alternatives, and
available ASR/runtime signals. `RiskAtomWeight(v)` is a risk-atom class weight
defined by the decision-critical atom schema. `DecisionDistance` maps the
downstream label space into an ordinal safety distance over `no_escalation`,
`review`, `priority_review`, `critical_escalation`, conservative machine
action, and abstention, with critical misses treated as the highest-risk
direction for conservative action.

### Downstream Decision Function

The downstream decision function `f` is fixed before CEIS scoring. It maps each
transcript or plausible variant into a declared triage action:

```text
f(transcript) in {
    no_escalation,
    manual_review,
    priority_review,
    critical_escalation,
    conservative_machine_action,
    abstain
}
```

The distance function is policy-aligned rather than language-model-generated:
same-action pairs have distance 0, neighboring review/escalation states have
distance 1, and movement from no escalation or routine handling to critical
escalation receives the largest distance. Unsafe downrouting of a critical
event receives the maximum penalty used by the policy replay. The method
contract is versioned in `docs/downstream_decision_contract.md` and
`80_semantic_risk_asr/scoring/ceis_config.json` so CEIS rankings can be
reconstructed from aggregate artifacts.

### CEIS Scale Discipline

All CEIS components are treated as bounded comparison terms, not calibrated
probabilities. `Plausibility(v | x)` is a proxy plausibility score; the paper
does not claim an acoustic posterior unless a later implementation supplies
one. `RiskAtomWeight(v)` and `DecisionDistance(f(x), f(v))` must be normalized
or tabulated before final submission. The next method-hardening analyses are:
uniform-weight ablation, no-plausibility ablation, binary-decision-flip
ablation, max versus top-k mean aggregation, and CEIS behavior by atom class.
Those analyses can be added only from aggregate-safe recomputation or reported
as planned validation if the current artifact package cannot reconstruct them.

Thresholds reported in the current predictor table are diagnostic operating
points selected on the scoped reviewed audit. They are useful for aggregate
comparison and reviewer inspection, but they are not frozen deployment
thresholds unless later selected on a separate development set.

Recovery remains automatic and machine-bounded. Human review is used as an
evaluation and governance layer, not as the proposed recovery method. The
recovery policies compare no recovery, confidence-only trigger, SRES-triggered
recovery, CEIS-triggered conservative action, and CEIS ensemble arbitration.

### Risk Atom Schema

The risk atom schema focuses on decision-critical spans:

| Risk atom | Decision role | Example effect |
| --- | --- | --- |
| Negation | reverses event state | transfer vs no transfer |
| Amount | changes severity | 30,000 vs 300,000 |
| Action | changes case stage | asking vs reporting vs transferring |
| Actor | changes scam interpretation | bank, police, family, customer service |
| Time | changes urgency | today, yesterday, next week |
| Intent | changes routing | inquiry, report, complaint |
| Uncertainty | changes confidence and safe action | sure, maybe, not sure |
| Scam pattern | changes case type | investment, fake police, installment cancellation |

### Counterfactual Variant Contract

Counterfactual variants are plausible ASR alternatives concentrated around
risk atoms. They are not generic paraphrases. A variant can be supported by
acoustic ambiguity, Mandarin phonetic confusion, domain-slot alternatives, or
model disagreement. The paper-facing claim is not that every possible variant
is enumerated; it is that the generated alternatives make downstream
decision-instability measurable.

### Recovery Policy Contract

The five-policy recovery experiment is:

1. no recovery;
2. confidence-only trigger;
3. SRES-triggered recovery;
4. CEIS-triggered conservative action;
5. CEIS ensemble arbitration.

The scoped recovery claim is evaluated only on aggregate human-reviewed
selected-300 evidence. Per-row details stay local or ignored. At the policy
layer, both SRES-triggered recovery and CEIS-triggered conservative action are
reported as risk-triggered conservative policies; CEIS's distinct contribution
is evaluated primarily in the predictor layer and in its decision-stability
framing.

### Reproducibility Layer

The paper-facing ASR surface metric is `cer_zh_micro`. The supplemental word
metric is `wer_zh_jieba_micro`. Raw whitespace WER and legacy stored WER fields
are audit-only because they are unstable for unsegmented Chinese transcripts.

The metric policy is validated by
`70_experiments/runs/wer_metric_audit_2026_05_25/`, which records manifest
checks, zero-reference-unit checks, tokenizer and normalization policy, and
`jiwer` cross-checks.

The target transcription locale is Taiwan Traditional Chinese. New candidate
models must satisfy the strict Taiwan Traditional Chinese locale gate before
promotion. Previously completed comparable baselines are retained only as
disclosed baselines, with locale-violation counts reported and no promotion
claim attached. Post-decode OpenCC or other conversion can be evaluated only as
a deployment repair lane; it cannot be used to claim that the raw ASR model
passed the locale gate.

Selected-300 human audit evidence is tracked through aggregate outputs. The
local transcript-bearing reviewer sheets, merged sheets, and completed package
remain outside the committed release boundary. The reviewed scope is risk
atoms, decision-change labels, expected safe action, confidence, per-model
assessment fields, and per-row timing. The current aggregate status is
dual-reviewer complete: reviewer 1 and reviewer 2 each completed 300/300
row-level records and 900/900 model-level assessments. Cohen's kappa is
0.849970 for decision-change, 1.000000 for semantic-risk label, 0.851426 for
expected safe action, and 0.934274 for annotation confidence.

All paper-facing claims point to aggregate artifacts. Raw audio, raw
transcripts, selected row IDs, hypotheses, reviewer notes, and model weights
remain governed local materials.

### Evaluation Units And N-Ladder

The manuscript separates evidence units explicitly so that model assessments
are not mistaken for independent audio rows.

| Layer | Unit | N | Role |
| --- | ---: | ---: | --- |
| Test split | audio rows | 258 | ASR model comparison |
| Selected high-stakes provenance | selected candidate rows / outputs | 300 | row-selection and provenance |
| Human-reviewed audit rows | audio rows | 300 | dual-reviewer decision-critical review unit |
| Human-reviewed model assessments | model-row assessments | 900 per reviewer | reviewer agreement and full selected-300 audit evidence |

Because model assessments are clustered within selected audio rows,
inferential uncertainty should be estimated with row-clustered bootstrap
resampling or leave-one-row-out sensitivity analysis. The completed 300-row
dual-reviewer audit strengthens the reliability layer; any predictor or
recovery table regenerated from the full audit should keep the row-clustered
design rather than treating model-level assessments as independent calls.

### Selection Provenance And Enrichment

The selected-300 audit surface is an enriched high-stakes sample, not a
prevalence-preserving sample of all anti-fraud calls. The selection summary
uses aggregate-safe provenance signals from SRES scoring, CEIS scoring, and
downstream escalation decisions, including high-risk missed, critical miss,
unsafe downrouting, model disagreement, high proxy risk, risk-score fill, and
clean-control strata. The aggregate selection thresholds recorded for the
current package are `low_wer_threshold=10.0`, `sres_threshold=20.0`, and
`ceis_threshold=5.0`.

Predictor results therefore support metric behavior on an enriched high-stakes
audit surface rather than population-level risk prevalence. If a submission
emphasizes CEIS/SRES separation, a sensitivity check should exclude rows
directly selected by CEIS or SRES family signals and confirm whether the same
directional pattern remains.

### Variant Coverage And Human Review Reliability

The current aggregate-only coverage audit reports CEIS top-atom proxy coverage
on the existing replay surface. It records aggregate proxy observations with
top-atom counts of negation 47, amount 37, action 3, and actor 3. The completed
selected-300 dual-reviewer audit provides the final submission validation
layer, while the reviewed selection surface also covers risk-signal atoms in
aggregate: action 25, actor 15, amount 23, negation 14, and scam pattern 23
selected rows. These counts support submission-safe coverage auditing, not
release of variant text. Source-specific coverage is
available for model-disagreement provenance in aggregate; phonetic,
domain-slot, runtime-signal, rejected-variant, and full variant-generation logs
are not currently reconstructed as release artifacts. Stronger generator claims
therefore require a future aggregate variant-generation log.

Human labels now include a completed dual-reviewer audit across the full
selected-300 surface. Both reviewers completed all row-level and model-level
fields, required fields have no empty values, row-level `yes` decisions have
at least one model-level `yes` or `uncertain`, critical atoms are contained in
risk atoms, and `yes` rows have expected safe action other than `none`. The
agreement layer records Cohen's kappa of 0.849970 for decision-change,
1.000000 for semantic-risk label, 0.851426 for expected safe action, and
0.934274 for confidence. This turns human audit reliability from a planned
extension into a reviewer-visible contribution.

## Experiments

Experiment 1 evaluates comparable ASR model evidence on the canonical 258-row
test split. This table supports model-comparison and split evidence, not the
paper-grade selected-300 risk/recovery claims.

Experiment 2 uses selected-300 high-stakes proxy outputs as input provenance.
The selected-300 proxy outputs identify an enriched high-stakes evidence
surface and the review sample, but their raw rows and transcript-bearing metric
inputs remain local or ignored. This experiment supports selection provenance,
not population prevalence.

Experiment 3 evaluates WER, CER, SRES, and CEIS against human-reviewed
decision-change labels from the selected-300 audit. The latest human audit
gate is complete at 300 rows with 900 model-level assessments per reviewer and
dual-reviewer agreement summaries. The current predictor table reports the
existing aggregate replay surface and should be regenerated from the completed
audit before final CSL submission so the full selected-300 reliability layer
and CEIS ablations are reflected in the final numbers.

Experiment 4 evaluates five recovery policies against the same human-reviewed
evidence layer. This is aggregate policy replay evidence for conservative
action and recovery governance; a live deployment trial is a later validation
layer.

Candidate ASR and multimodal models are kept in a separate exploratory lane.
They must not enter the main ASR table until they pass field-contract,
runtime-validity, and Taiwan Traditional Chinese locale gates in order.

## Results

The Results section separates comparable ASR evidence, candidate-lane
boundaries, human-reviewed predictor evidence, and human-reviewed recovery
evidence. This separation preserves claim-evidence alignment: the main ASR
benchmark supports model-comparison context, while selected-300 human-reviewed
outputs support paper-grade risk and recovery claims.

Human review supplies evaluation labels only. The proposed recovery policies
are automatic, aggregate-evaluated policies; no transcript-bearing row content
is required for paper-facing claims.

### Table 1. Main ASR Benchmark Table

Table 1 reports six comparable ASR runs on the canonical 258-row split. The
paper-facing primary ASR metric is `cer_zh_micro`; `wer_zh_jieba_micro` is
reported as the supplemental segmented word metric. Unsafe downrouting and
high-risk missed counts are scope-controlled split/model-comparison evidence,
not the final selected-300 human-reviewed risk claim.

Only models with completed comparable 258-row split evidence are included.

| Run | Model family | Rows | `cer_zh_micro` | `wer_zh_jieba_micro` | Unsafe downrouting | High-risk missed | Locale violation rows | Paper use |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `breeze_asr25_partial_encoder_legacy_best_test_split` | Breeze-ASR-25 partial encoder | 258 | 15.04 | 21.53 | 7 | 4 | 0 | Scope-controlled split/model comparison |
| `breeze_asr25_lora_legacy_best_test_split` | Breeze-ASR-25 LoRA | 258 | 18.23 | 25.59 | 10 | 7 | 0 | Scope-controlled split/model comparison |
| `breeze_asr25_base_test_split` | Breeze-ASR-25 base | 258 | 22.72 | 30.39 | 34 | 30 | 0 | Scope-controlled split/model comparison |
| `breeze_asr26_test_split` | Breeze-ASR-26 | 258 | 24.27 | 32.29 | 27 | 22 | 0 | Optional dialect-aware comparator |
| `whisper_large_v2_test_split` | Whisper large-v2 | 258 | 24.72 | 32.23 | 33 | 28 | 1 | Comparable ASR baseline |
| `whisper_small_test_split` | Whisper small | 258 | 34.86 | 43.44 | 76 | 70 | 4 | Comparable ASR baseline |

Evidence source:
`70_experiments/runs/janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv`.

The legacy Breeze-ASR-25 partial encoder is the strongest current hypothesis
generator on the 258-row split, with the lowest
`cer_zh_micro` and the lowest unsafe downrouting and high-risk missed counts
among the six comparable runs. This supports using it as a strong ASR evidence
layer while keeping final risk and recovery claims tied to the human-reviewed
selected-300 outputs.

### Table 2. Candidate And Exploratory Lane

Table 2 reports bounded candidate-lane evidence for models that are not
promoted to the main 258-row or selected-300 tables. These gates document
feasibility, locale behavior, and runtime constraints without mixing
exploratory candidates with comparable ASR baselines.

These models are bounded negative, feasibility, or runtime evidence. They do
not enter the main ASR benchmark table.

| Candidate | Current gate | Rows | `cer_zh_micro` | `wer_zh_jieba_micro` | Locale/runtime result | Decision |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Whisper large-v3 | Fixed 15-row contract | 15 | 33.33 | 42.04 | 2 locale-violation rows, 23 simplified chars | Do not promote to 258-row or selected-300 |
| Whisper large-v3-turbo | Fixed 15-row contract | 15 | 40.36 | 50.87 | 4 locale-violation rows, 48 simplified chars | Retain as bounded feasibility evidence only; no split-level or selected-300 claim |
| SenseVoiceSmall | Fixed 15-row contract | 15 | 63.12 | 78.98 | 14 locale-violation rows, 209 simplified chars | Reject from full split until locale policy changes |
| Qwen3-ASR-0.6B | Fixed 15-row contract | 15 | 64.16 | 81.07 | 15 locale-violation rows, 260 simplified chars | Reject from full split until locale policy changes |
| Qwen3-ASR-1.7B | Bounded load gate | 0 | n/a | n/a | Timeout before inference at fetch/load after about 60.07s | Retry only after isolated cache/download plan |
| Gemma 4 E2B/E4B | Local multimodal class probe | 0 | n/a | n/a | Local Transformers 4.57.6 has no required Gemma 4 multimodal/audio class | Build isolated prompted multimodal runtime before testing |

Evidence sources:
`70_experiments/runs/asr_candidate_current_recheck_2026_05_26/candidate_current_recheck_summary.tsv`
and `70_experiments/runs/asr_candidate_current_recheck_2026_05_26/summary.json`.

Whisper large-v3, Whisper large-v3-turbo, SenseVoiceSmall, and Qwen3-ASR-0.6B
have field-contract evidence but fail strict Taiwan Traditional Chinese locale
promotion criteria. Qwen3-ASR-1.7B remains stopped before inference at
fetch/load, and Gemma 4 E2B/E4B remain blocked by local multimodal runtime
support. The next validation layer is locale/runtime promotion, not a broader
full-split ASR run.

### Table 3. Human-Reviewed Predictor Table

Table 3 reports the current aggregate predictor comparison against
human-reviewed `human_decision_change_yes` labels. WER/CER are
transcript-surface baselines; SRES is the semantic-risk baseline; CEIS is the
proposed decision-stability metric. The completed 300-row dual-reviewer audit
is the upgraded final-submission evidence surface, so Table 3 should be
regenerated with the full audit and the CEIS ablation suite before CSL
submission.

Target: `human_decision_change_yes` on the current aggregate replay surface.
Diagnostic thresholds are selected on the scoped audit set for aggregate
comparison and are not frozen deployment thresholds. The final CSL table should
report the positive-label count under the completed dual-reviewer audit.

| Predictor | Unit | AUC | Row-clustered AUC 95% CI | Diagnostic threshold | Best F1 | Row-clustered F1 95% CI | Precision | Recall | False negative | Paper use |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| WER | 90 model assessments / 30 rows | 0.6964 | 0.5699-0.8125 | 42.59 | 0.4615 | 0.2857-0.6667 | 0.3913 | 0.5625 | 7 | Surface baseline |
| CER | 90 model assessments / 30 rows | 0.7276 | 0.6084-0.8372 | 16.42 | 0.4516 | 0.3158-0.6667 | 0.3043 | 0.8750 | 2 | Surface baseline |
| SRES total | 90 model assessments / 30 rows | 0.8995 | 0.8119-0.9657 | 270.0 | 0.6512 | 0.4667-0.8421 | 0.5185 | 0.8750 | 2 | Semantic-risk baseline |
| CEIS max | 90 model assessments / 30 rows | 0.9117 | 0.8516-0.9615 | 5.0 | 0.6275 | 0.4681-0.8148 | 0.4571 | 1.0000 | 0 | Proposed decision-stability metric |

Evidence source:
`70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_comparison.tsv`.
Row-clustered uncertainty source:
`70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_clustered_ci.tsv`.
Leave-one-row-out sensitivity source:
`70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_leave_one_row_out.tsv`.

CEIS has the strongest point-estimate human-reviewed decision-change AUC and
reaches recall 1.0 at the diagnostic threshold, while SRES achieves the highest
best-threshold F1 and fewer false positives. This is the paper's central
contribution pattern: CEIS exposes conservative decision instability, SRES
remains a strong semantic-risk baseline, and the full selected-300 audit plus
ablations provide the next reviewer-facing validation layer.

### Table 4. Human-Reviewed Recovery Policy Table

Table 4 reports five recovery policies evaluated as aggregate replay under
human-reviewed selected-300 labels. The recovery evidence is aggregate-only and
uses the same current replay surface as the predictor table.

Evidence mode: human-reviewed selected-300 aggregate replay, with full
300-row dual-reviewer regeneration as the final CSL validation layer.

| Policy | Model assessments | Unsafe downrouting | High-risk missed | Critical miss | Recovery budget | Row-clustered budget 95% CI | Severe misses eliminated | Row-clustered severe-miss 95% CI | Triggers per severe miss eliminated | Scoped interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| No recovery | 90 | 29 | 6 | 1 | 0.0000 | 0.0000-0.0000 | 0 | 2-13 remaining severe misses | n/a | Baseline decision risk |
| Calibrated-confidence unavailable | 90 | 29 | 6 | 1 | 0.0000 | 0.0000-0.0000 | 0 | 2-13 remaining severe misses | n/a | No calibrated confidence trigger available |
| SRES-triggered recovery | 90 | 24 | 0 | 0 | 0.3889 | 0.3000-0.4889 | 7 | 0-0 remaining severe misses | 5.0 | Semantic-risk recovery baseline |
| CEIS-triggered conservative action | 90 | 24 | 0 | 0 | 0.3889 | 0.3000-0.4889 | 7 | 0-0 remaining severe misses | 5.0 | Matches SRES severe-miss elimination at same budget in replay |
| CEIS ensemble arbitration | 90 | 24 | 0 | 0 | 0.5222 | 0.4000-0.6556 | 7 | 0-0 remaining severe misses | 6.7 | Adds abstention/interval behavior at higher budget |

Evidence sources:
`70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/policy_comparison.tsv`
and `70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/summary.json`.
Row-clustered uncertainty source:
`70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/policy_comparison_clustered_ci.tsv`.
Leave-one-row-out sensitivity source:
`70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/policy_comparison_leave_one_row_out.tsv`.
Fixed-budget frontier source:
`70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/fixed_budget_recovery_frontier.tsv`.

Without recovery, the reviewed evidence contains 6 high-risk misses and 1
critical miss. SRES-triggered recovery and CEIS-triggered conservative action
both eliminate high-risk missed and critical miss counts in aggregate policy
replay at the same 0.3889 trigger budget, corresponding to 35 triggers for 7
severe missed outcomes eliminated. CEIS ensemble arbitration preserves this
0/0 result while introducing abstention behavior at a higher 0.5222 budget. The
policy replay eliminates the most severe missed-risk outcomes under the scoped
labels, while residual unsafe downrouting remains at 24 and requires separate
governance.

A fixed-budget replay provides an additional operating view. At 10%, 20%, 30%,
and 40% requested trigger budgets, CEIS-ranked conservative replay leaves 0
high-risk misses and 0 critical misses under the scoped labels; the 10% point
uses 9 triggers. SRES-ranked conservative replay leaves 4, 2, 2, and 0 severe
missed outcomes at the same requested budgets, reaching 0 severe misses only
when all 35 eligible SRES triggers are used. This frontier supports CEIS as a
conservative decision-stability signal while preserving the Table 4 result that
the diagnostic SRES and CEIS policies tie at the selected 0.3889 budget.
Appendix Table A1 reports the fixed-budget replay explicitly as an
operating-point frontier rather than a deployment-threshold claim.

## Figure Package

The figure package is generated from aggregate-only inputs by
`80_semantic_risk_asr/paper/generate_paper_figures.R`. The Python entrypoint
`80_semantic_risk_asr/paper/generate_paper_figures.py` remains only as a
compatibility wrapper that calls the R script. The generated SVGs and PDF
exports and their privacy boundary are listed in
`80_semantic_risk_asr/paper/figures/`.
The aggregate artifact manifest is generated by
`80_semantic_risk_asr/paper/build_artifact_manifest.py` and written to
`80_semantic_risk_asr/paper/artifact_manifest.tsv`.

| Figure | File | Caption | Source | Privacy boundary |
| --- | --- | --- | --- | --- |
| F1. CDS-ASR pipeline | `figures/f1_cds_asr_pipeline.svg` | CDS-ASR converts audio into ASR hypotheses and runtime signals, extracts risk atoms, generates plausible variants, scores SRES/CEIS, and applies constrained recovery or conservative action. | Method section | No transcript text or row content |
| F2. Evidence boundary | `figures/f2_evidence_boundary.svg` | The manuscript separates 258-row split/model-comparison evidence, selected-300 provenance evidence, and selected-300 human-reviewed predictor/recovery evidence. | publishable evidence summary | Aggregate status only |
| F3. Predictor AUC | `figures/f3_predictor_auc.svg` | CEIS has the highest human-reviewed decision-change AUC in the scoped selected-300 audit, while SRES remains strongest on best-threshold F1; Table 3 reports row-clustered uncertainty. | `human_audit_predictor_comparison.tsv` | Aggregate predictor metrics |
| F4. Recovery outcomes | `figures/f4_recovery_outcomes.svg` | SRES-triggered recovery and CEIS-triggered conservative action both eliminate high-risk missed and critical miss counts in aggregate replay at the same 0.3889 budget. | `policy_comparison.tsv` | Aggregate policy counts |
| F5. Model lane state | `figures/f5_model_lane_state.svg` | Main comparable split evidence, locale-gated candidates, and runtime-blocked probes remain separate until promotion gates are satisfied. | main/candidate aggregate summaries | Aggregate lane state |
| F6. N-ladder | `figures/f6_n_ladder.svg` | The evidence chain separates 258 rows, selected-300 provenance, completed 300-row dual-reviewer audit, and 900 model-level assessments per reviewer. | method evidence units | Aggregate counts only |
| F7. Budget-risk frontier | `figures/f7_budget_risk_frontier.svg` | Fixed-budget policy replay shows the trigger-budget tradeoff needed to eliminate severe missed outcomes under scoped labels. | `fixed_budget_recovery_frontier.tsv` | Aggregate policy counts |
| F8. Low-WER danger signals | `figures/f8_low_wer_danger.svg` | Low-WER rows can still carry label-flip, unsafe-downrouting, and conservative-trigger signals, directly supporting the title claim that low WER can remain operationally dangerous. | `low_wer_danger_summary.tsv` | Aggregate proxy counts |
| F9. Risk-atom instability heatmap | `figures/f9_risk_atom_instability_heatmap.svg` | Instability concentrates differently by ASR model and decision-critical atom, showing the mechanism behind CEIS/SRES risk signals. | `risk_atom_instability.tsv` | Aggregate proxy counts |
| F10. Human-reviewed risk-atom outcomes | `figures/f10_human_reviewed_atom_outcomes.svg` | Human review connects risk-atom coverage to criticality and decision-change evidence across reviewed rows. | `human_audit_risk_atom_review.tsv` | Aggregate human-reviewed counts |
| F11. Risk-atom entropy heatmap | `figures/f11_risk_atom_entropy_heatmap.svg` | Atom-class entropy summarizes whether instability is concentrated in a few atom classes or distributed across several atom classes. | `risk_atom_instability.tsv` | Aggregate entropy from atom counts |

Submission-package PDF exports are generated with the same basename under
`80_semantic_risk_asr/paper/figures/`.

Word-level confusion entropy is a valuable next analysis, especially for
frequently misrecognized decision words around negation, amount, transfer
action, actor identity, and scam-pattern cues. The current submission package
keeps that analysis out of the public figure set unless it is first converted
into a redacted aggregate lexicon with no transcript spans, audio IDs, selected
row IDs, hypotheses, or reviewer notes. The R-generated F11 is therefore the
publishable entropy layer for the current evidence boundary, while a future
local-only confusion lexicon can support a supplemental word-level entropy
heatmap after privacy review.

## Discussion

The evidence supports a consequence-centered ASR evaluation claim: correct
WER/CER reporting is necessary, but transcript similarity alone does not
capture high-stakes decision instability. The reviewed selected-300 predictor
table shows that SRES and CEIS align more strongly with human-reviewed
decision-change labels than WER/CER in this scoped evidence layer.

The model comparison should be presented as an evidence layer, not as a model
leaderboard. The partial encoder is the strongest current ASR hypothesis
generator on the comparable split, and the selected-300 human-reviewed evidence
shows how downstream decision evidence refines transcript-centered model
comparison.

The recovery result supports a scoped replay claim. Under human-reviewed
selected-300 labels, risk-triggered conservative policies, including
CEIS-triggered conservative action, eliminate high-risk missed and critical
miss counts in aggregate replay. SRES-triggered recovery and CEIS-triggered
conservative action reach this result at the same 0.3889 trigger budget, while
ensemble arbitration adds interval/abstention behavior as a higher-budget
governance option. CEIS is therefore best presented as the more conservative
decision-instability signal at the predictor layer, while SRES remains a
strong semantic-risk recovery baseline.

Improving ASR remains necessary, but stronger transcript models do not replace
decision-stability analysis. The paper studies residual instability after
transcript scoring: whether plausible ASR alternatives around decision atoms
would change escalation, routing, or conservative action. This makes CDS-ASR a
safety layer for the remaining decision interval, not a substitute for ASR
model improvement.

The aggregate-only artifact boundary is also a contribution to reproducible
governance. The paper does not claim full public row-level reproducibility.
Instead, it provides aggregate reproducibility, operation records, validation
gates, and consistency checks under a privacy-preserving audit boundary.

The candidate lane is already bounded by evidence. Whisper large-v3,
Whisper large-v3-turbo, SenseVoiceSmall, and Qwen3-ASR-0.6B have small-gate
evidence but fail strict Taiwan Traditional Chinese locale promotion criteria.
Qwen3-ASR-1.7B is stopped by fetch/load timeout, and Gemma 4 E2B/E4B require an
isolated multimodal runtime. The next validation step is locale/runtime
validation, not a broader full-split ASR run.

## Claim Registry

| Claim | Scope | Evidence artifact | Statistic | Limitation / defense |
| --- | --- | --- | --- | --- |
| CEIS has the strongest AUC among reported predictors | Current aggregate replay surface; regenerate on completed 300-row dual-reviewer audit before final CSL submission | `human_audit_predictor_comparison.tsv` | AUC 0.9117 | Decision-stability signal; full-audit ablation pending |
| CEIS reaches a zero-FN operating point | scoped selected-300 diagnostic threshold | `human_audit_predictor_comparison.tsv` | FN 0, recall 1.0000 | Retrospective diagnostic threshold, not frozen deployment threshold |
| SRES and CEIS conservative policies eliminate severe misses in replay | aggregate policy replay over reviewed assessments | `policy_comparison.tsv` | high-risk missed 0, critical miss 0 | Replay evidence, not live causal deployment; policies tie at 0.3889 budget |
| Partial encoder is the strongest current ASR hypothesis generator | 258-row split/model-comparison layer | `asr_cds_proxy_comparison.tsv` | `cer_zh_micro` 15.04, unsafe downrouting 7, high-risk missed 4 | Split-level model-comparison context only |
| Selected-300 is a high-stakes audit surface | enriched selection provenance | `human_audit_selection_summary.json`, `selection_strata.tsv` | 300 candidates, 300 reviewed rows, 900 model-level assessments per reviewer | Enriched audit surface; selection provenance disclosed |
| Dual-reviewer audit supports label reliability | completed selected-300 review | `human_audit_reviewer_agreement_summary.json`, `human_audit_reviewer_agreement.tsv` | Cohen's kappa 0.849970-1.000000 across key fields | Transcript-bearing reviewer sheets remain local |
| Aggregate-only release supports reviewer-visible auditability | release and operation-record layer | validation summaries, evidence matrices, operation records, figure scripts | gate state: roadmap complete, publishable ready, consistency 26/26 | Public auditability with governed local transcript-bearing evidence |

## Ethics, Privacy, And Intended Use

This study treats transcript-bearing speech data as sensitive operational
content. NIH human-subjects guidance treats the use, study, analysis, or
generation of identifiable private information as a human-subjects trigger
under the cited federal definition [@nih_human_subjects_research_2024]. This
paper therefore keeps raw audio, transcript-bearing hypotheses, reviewer
notes, row identifiers, local response sheets, and runtime logs outside the
release boundary. Before any external data release or deployment claim, the
institutional review, exemption, data-use, retention, encryption, and access
control status must be documented.

CDS-ASR is intended for ASR safety audit, risk-aware routing, manual-review
prioritization, conservative escalation, and machine abstention. It is not
intended for automatic guilt or fraud determination, automatic account
freezing, service denial, punitive action, or direct law-enforcement reporting
without human review. "Conservative machine action" means preserving
uncertainty, raising review priority, abstaining, or requiring human
confirmation.

This intended-use boundary aligns the paper with risk-management governance
rather than autonomous adverse decision-making. NIST describes the AI RMF as a
voluntary framework for managing AI risks to individuals, organizations, and
society and for incorporating trustworthiness considerations into AI design,
development, use, and evaluation [@nist_ai_rmf_2026]. For cross-border or
future deployment contexts, the EU AI Act illustrates the broader regulatory
direction toward risk-based obligations and high-risk AI governance
[@eu_ai_act_2026]. This manuscript does not provide legal compliance analysis;
it provides a scoped consequence-centered audit method and a privacy-preserving
release boundary.

## Limitations And Threats To Validity

The human-reviewed evidence now covers the full selected-300 surface with two
reviewers and 900 model-level assessments per reviewer. This supports a
stronger high-stakes audit and reviewer-agreement claim while leaving
population-level deployment prevalence to a later study.

Model-level assessments are clustered within selected audio rows and should
not be treated as independent calls. The current submission-prep package
reports row-clustered bootstrap intervals and leave-one-row-out sensitivity
tables for the existing predictor and recovery metrics; the full 300-row
dual-reviewer audit should be used to regenerate final CSL predictor,
recovery, and ablation tables.

The number of positive decision-change cases remains a key calibration handle.
The final CSL table should report the positive-label count under the completed
dual-reviewer audit and preserve row-clustered uncertainty for AUC and
threshold behavior.

The selected-300 audit surface is deliberately enriched for high-stakes
signals. It supports decision-stability behavior within the selected audit
boundary, not population prevalence of ASR-induced harm across all calls.

The reported best thresholds are diagnostic operating points on the scoped
reviewed audit. They can overstate deployment performance unless threshold
selection is later frozen on a separate development set.

Human labels now include a completed dual-reviewer audit and reviewer-agreement
summary. Cohen's kappa is 0.849970 for decision-change, 1.000000 for
semantic-risk label, 0.851426 for expected safe action, and 0.934274 for
annotation confidence. The next validation layer is full-table regeneration
and CEIS ablation, not additional reviewer recruitment.

Recovery evidence is aggregate-only. This protects transcript-bearing call and
review content, but limits external row-level reproducibility.

CEIS depends on generated plausible variants and risk atom weights. Missed
variants or misweighted atoms can affect instability scoring. The current
aggregate package records risk-atom coverage and a variant-coverage status
table, but a full source-specific aggregate variant generation audit remains a
planned validation extension.

The Taiwan Traditional Chinese locale policy is strict by design. Candidate
model rejection may reflect deployment-locale mismatch, not universal ASR
inferiority.

Recovery policies eliminate high-risk missed and critical miss counts in
aggregate replay, but Table 4 still leaves unsafe downrouting count at 24 after
SRES/CEIS conservative recovery. The evidence supports scoped severe-miss
reduction, not elimination of all safety risk.

The study does not include a deployment trial and does not estimate population
prevalence of ASR-induced harm across all calls. It evaluates whether
decision-critical ASR risk can be detected and mitigated within a deliberately
enriched high-stakes audit surface.

## Appendix / Artifact Availability

### Artifact Availability Statement

The repository release includes aggregate run records, validation summaries,
metric tables, evidence matrices, figure-generation code, and paper-facing
documentation. Raw audio, raw transcripts, selected row identifiers, audio
identifiers, model hypotheses, transcript-bearing runtime logs, reviewer
response sheets, reviewer notes, and model weights are not released because
they may contain sensitive call or review content.

Because transcript-bearing materials may contain sensitive call content,
reproducibility is provided through aggregate validation artifacts, operation
records, manifest checks, and consistency audits rather than through raw row
release. This provides reviewer-visible auditability for model comparison,
metric policy, selected-300 human-review status, predictor analysis,
recovery-policy evaluation, candidate-lane boundaries, and consistency checks
while preserving the local-only boundary for sensitive materials.

The reviewer package should include an aggregate manifest with artifact path,
role, privacy class, generator, source inputs, SHA256, source git commit,
timestamp, Python version, metric-library versions, tokenizer policy, locale
normalization policy, decoding parameters where available, random seeds where
used, and hardware summary. The manifest records auditability metadata without
adding transcript-bearing row content.

### Reviewer-Reproducible Aggregate Artifacts

- Artifact manifest:
  `80_semantic_risk_asr/paper/artifact_manifest.tsv`
- Artifact manifest generator:
  `80_semantic_risk_asr/paper/build_artifact_manifest.py`
- Experiment registry: `70_experiments/registry.tsv`
- Main 258-row comparison:
  `70_experiments/runs/janus_258_test_split_asr_cds_proxy/asr_cds_proxy_comparison.tsv`
- Metric-definition audit:
  `70_experiments/runs/wer_metric_audit_2026_05_25/journal_compliance_summary.json`
- Selected-300 human audit refresh:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_refresh_summary.json`
- Human-reviewed predictor evidence:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_comparison.tsv`
- Human-reviewed predictor row-clustered CI:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_clustered_ci.tsv`
- Human-reviewed predictor leave-one-row-out sensitivity:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_predictor_leave_one_row_out.tsv`
- Human-reviewed recovery evidence:
  `70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/policy_comparison.tsv`
- Human-reviewed recovery row-clustered CI:
  `70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/policy_comparison_clustered_ci.tsv`
- Human-reviewed recovery leave-one-row-out sensitivity:
  `70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/policy_comparison_leave_one_row_out.tsv`
- Human-reviewed recovery fixed-budget frontier:
  `70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/fixed_budget_recovery_frontier.tsv`
- Claim registry:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/claim_registry.tsv`
- CEIS method summary:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/ceis_method_summary.tsv`
- Selection provenance summary:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/selection_provenance_summary.tsv`
- Counterfactual variant coverage status:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/counterfactual_variant_coverage_summary.tsv`
- Post-review evidence checklist:
  `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_post_review_evidence_summary.json`
- Publishable evidence audit:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/publishable_evidence_completion_summary.json`
- Consequence evidence matrix:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/consequence_evidence_matrix.tsv`
- Roadmap completion audit:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/postdoc_roadmap_completion_summary.json`
- Evidence-chain consistency audit:
  `70_experiments/runs/postdoc_evidence_chain_2026_05_25/evidence_chain_consistency_summary.json`
- Candidate bounded recheck:
  `70_experiments/runs/asr_candidate_current_recheck_2026_05_26/summary.json`

### Appendix Table A1. Fixed-Budget Recovery Frontier

The fixed-budget frontier is a retrospective aggregate replay over the same 90
reviewed model assessments. It reports what remains after applying ranked
conservative triggers at requested trigger budgets. Requested 40% budget maps
to 35 eligible triggers, so the observed budget is 0.3889.

| Score metric | Requested budget | Triggered | Observed budget | Unsafe downrouting | High-risk missed | Critical miss | Severe missed | Severe misses eliminated | Triggers per severe miss eliminated |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SRES total | 0.1000 | 9 | 0.1000 | 28 | 4 | 0 | 4 | 3 | 3.0 |
| SRES total | 0.2000 | 18 | 0.2000 | 26 | 2 | 0 | 2 | 5 | 3.6 |
| SRES total | 0.3000 | 27 | 0.3000 | 26 | 2 | 0 | 2 | 5 | 5.4 |
| SRES total | 0.4000 | 35 | 0.3889 | 24 | 0 | 0 | 0 | 7 | 5.0 |
| CEIS | 0.1000 | 9 | 0.1000 | 24 | 0 | 0 | 0 | 7 | 1.2857 |
| CEIS | 0.2000 | 18 | 0.2000 | 24 | 0 | 0 | 0 | 7 | 2.5714 |
| CEIS | 0.3000 | 27 | 0.3000 | 24 | 0 | 0 | 0 | 7 | 3.8571 |
| CEIS | 0.4000 | 35 | 0.3889 | 24 | 0 | 0 | 0 | 7 | 5.0 |

Evidence source:
`70_experiments/runs/janus_300_high_stakes_recovery_human_reviewed_2026_05_26/fixed_budget_recovery_frontier.tsv`.

### Operation Records

The selected-300 reviewer route is documented through aggregate-only operation
records, including response closeout, response apply logs, reviewer work order,
post-review sequence, operation-record audit, and consistency audit. These
records provide command-level reproducibility without exposing transcript or
row content.

Key records:

- `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_response_closeout_summary.json`
- `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_batch_response_apply_log.tsv`
- `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_review_work_order_summary.json`
- `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_post_review_sequence_summary.json`
- `70_experiments/runs/janus_300_high_stakes_human_audit_selection_2026_05_25/human_audit_operation_record_summary.json`

### Privacy And Local-Only Boundary

The following stay local or ignored:

- raw audio;
- raw transcripts;
- selected sample IDs and audio IDs;
- transcript-bearing audit sheets and response sheets;
- reviewer notes;
- raw model hypotheses and predictions;
- transcript-bearing runtime logs;
- checkpoints, adapters, and model weights;
- local downloaded reviewer packets and zip files.

The tracked repo preserves aggregate counts, run records, validation summaries,
metric tables, and paper-facing evidence matrices. This boundary lets reviewers
audit the evidence chain while protecting transcript-bearing material.

## Validation Gate Commands

Run these after manuscript packaging changes:

```bash
.venv/bin/python 80_semantic_risk_asr/scoring/audit_postdoc_roadmap_completion.py --output-json /tmp/cib_roadmap_completion_check.json --output-tsv /tmp/cib_roadmap_completion_check.tsv
.venv/bin/python 80_semantic_risk_asr/scoring/audit_publishable_evidence_chain.py --output-json /tmp/cib_publishable_check.json --output-tsv /tmp/cib_publishable_check.tsv
.venv/bin/python 80_semantic_risk_asr/scoring/audit_evidence_chain_consistency.py --output-json /tmp/cib_consistency_check.json --output-tsv /tmp/cib_consistency_check.tsv
```

Expected current gate state:

- roadmap completion: `roadmap_complete=true`, `blocking_gate=none`;
- publishable evidence: `publishable_ready=true`;
- consistency audit: `26/26` checks pass, `failed_checks=[]`.

## Scope Control For Additional Experiments

Do not run new full-split ASR experiments now. Candidate models can move to
258-row or selected-300 only after strict Taiwan Traditional Chinese locale
policy is satisfied or an isolated Gemma 4 multimodal runtime exists. Until
then, the active work is manuscript drafting, results-table packaging,
artifact availability, citation completion, and submission readiness.
