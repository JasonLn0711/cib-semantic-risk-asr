# ASR-Control LoRA Payload Contract

Date: 2026-06-01

This record prepares the first ASR-control LoRA payload contract. It does not train an adapter.

## Decision

- Status: `lora_payload_contract_ready_training_not_started`
- First route: `qwen3_asr_1_7b_r16_a32_research_probe`
- Route type: `bounded_research_probe_lora`
- Model: `Qwen/Qwen3-ASR-1.7B`
- Rank/alpha: `16 / 32`
- Claim boundary: consequence probe only; no diagnostic-proven promotion claim.

The source ground truth is the already reviewed gold subset. Transcript-bearing manifests stay in the ignored runtime lane. Git tracks only aggregate counts, hashes, leakage decisions, and the smoke-route contract.

The leakage report records known overlap with the fixed-15 ASR-control baseline. This is acceptable for a bounded research probe, but it blocks using the same fixed-15 rows as clean promotion evidence after training.
