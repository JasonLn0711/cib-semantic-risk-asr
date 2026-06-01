# Qwen Auto Semantic-Damage Proxy

This run implements the auto-only replacement for the previous human semantic-damage review gate.
It reads raw and OpenCC/Taiwan-term repaired Qwen transcript-bearing payloads only from ignored local runtime lanes.
Tracked artifacts contain aggregate counts, gate status, and manifest hashes only.

## Decision

- Decision: `auto_only_no_winner_stop`
- Semantic-damage blocker count: `7`
- Locale residual rows: `7`
- Claim boundary: repaired-pipeline automatic-proxy evidence only; raw model capability remains separate.

## Proxy Checks

The proxy checks CER/WER worsening, new hallucination proxy, critical term / proper-noun changes, abbreviation changes, suspicious length-ratio changes, empty-output changes, locale residuals, and raw/repaired payload pairing.

## Privacy Boundary

Raw audio, row IDs, transcripts, references, hypotheses, repaired text, model outputs, reviewer notes, local paths, transcript-bearing logs, and cache paths are not tracked.
