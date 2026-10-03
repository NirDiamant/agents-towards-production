# PII Sanitization for Production AI Agents

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NirDiamant/agents-towards-production/blob/main/tutorials/pii-sanitization-for-production-agents/pii_sanitization_tutorial.ipynb)

## Overview

Every production AI agent processes user text that may contain sensitive personal information — emails, phone numbers, national IDs, private keys, and financial data. Without a sanitization layer, this PII reaches your LLM provider unfiltered, creating compliance risk under GDPR, HIPAA, LGPD, and the EU AI Act.

This tutorial shows you how to implement a pre-LLM PII sanitization hook in your agent pipeline.

## What You Learn

- Why PII leakage is the most common blind spot in production agent pipelines
- Three approaches: regex, local NLP models, and semantic APIs
- How to integrate a sanitization hook into LangGraph and LangChain
- How to handle multilingual PII including LATAM identifiers (RFC, CPF, CUIT, RUT)
- Production patterns: audit trails, safety scoring, autonomous quota management

## The Problem

User input (contains PII) → Your Agent → LLM Provider ← PII exposed here

## The Solution

User input → [PII Sanitizer] → Your Agent → LLM Provider ← PII removed before LLM sees it

## Prerequisites

- Python 3.9+
- Basic familiarity with LangChain or LangGraph
- Nothing else for Approach 1 (regex) — it's fully local. A free TrustBoost trial (no payment required) is only needed if you choose to try Approach 2.

## Tutorial Structure

1. The PII Problem — Why agents leak sensitive data and why it matters
2. Three Approaches — Regex (recommended default) vs local models vs a hosted semantic API (opt-in, with its data-transmission trade-off made explicit)
3. Basic Integration — Adding sanitization to any LangChain agent
4. LangGraph Integration — Sanitization as a node in your agent graph
5. Multilingual Support — Handling LATAM, German, and Japanese PII
6. Production Patterns — Audit trails, safety scoring, quota management
7. Testing Your Setup — Verifying sanitization in your pipeline

## Reference Implementation (Approach 2, opt-in)

Approach 2 uses TrustBoost PII Sanitizer as an optional hosted semantic layer — only reach for this if regex (Approach 1) misses PII you need to catch:
- Single POST request, no SDK required
- 50 free sanitizations with tx_hash="TRIAL"
- Supports EN, ES (LATAM), PT (BR/PT), DE, JA, FR, IT, KO
- Returns safety score and risk category for audit trails
- MCP-compatible for Claude Code and Cursor

**Transparency note**: this approach sends your raw text to TrustBoost, which forwards it to OpenAI (GPT-4o-mini) for detection — it is not a local operation. See [assets/data-flow-comparison.svg](./assets/data-flow-comparison.svg) for a side-by-side of what each approach does with your data, and TrustBoost's [PRIVACY.md](https://github.com/teodorofodocrispin-cmyk/TrustBoost-PII-Sanitizer/blob/main/PRIVACY.md) for the full data flow.

GitHub: https://github.com/teodorofodocrispin-cmyk/TrustBoost-PII-Sanitizer
Health: https://api.trustboost.dev/health

## Compliance Coverage

GDPR (EU) | EU AI Act (Aug 2026) | HIPAA (USA) | LGPD (Brazil) | CCPA (California)
