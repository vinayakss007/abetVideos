# ADR-002: edge-tts for Text-to-Speech

**Date:** 2026-06-02

## Status
Accepted

## Context
The application needs to generate voice narration for video scenes. Options: edge-tts (Microsoft Edge TTS), Google Cloud TTS, Amazon Polly.

## Decision
Use `edge-tts`, a Python library that uses Microsoft Edge's free TTS API.

## Rationale
- Free to use (no API key required, unlike Google/AWS)
- Natural-sounding neural voices with wide language support
- Simple async Python API (`edge_tts` via PyPI)
- No cloud vendor lock-in

## Consequences
- Positive: Zero cost for TTS generation
- Positive: Good voice quality (Microsoft Neural TTS)
- Negative: Relies on Microsoft's Edge endpoint (could change or be rate-limited)
- Negative: No streaming mode (generates full audio file, then returns)
