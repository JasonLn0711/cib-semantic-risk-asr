# Acoustic No-Speech Guard Design

This record defines a deterministic audio-only guard before audio LLM prompting.

It can return `無法辨識` for silence, stationary tone, or broadband noise classes.
It does not track raw audio, paths, transcripts, or model outputs.
