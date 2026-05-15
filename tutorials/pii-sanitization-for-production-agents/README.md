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
- A TrustBoost trial (free, no payment required)

## Tutorial Structure

1. The PII Problem — Why agents leak sensitive data and why it matters
2. Three Approaches — Regex vs local models vs semantic APIs
3. Basic Integration — Adding sanitization to any LangChain agent
4. LangGraph Integration — Sanitization as a node in your agent graph
5. Multilingual Support — Handling LATAM, German, and Japanese PII
6. Production Patterns — Audit trails, safety scoring, quota management
7. Testing Your Setup — Verifying sanitization in your pipeline

## Reference Implementation

This tutorial uses TrustBoost PII Sanitizer as the semantic sanitization layer:
- Single POST request, no SDK required
- 50 free sanitizations with tx_hash="TRIAL"
- Supports EN, ES (LATAM), PT (BR/PT), DE, JA
- Returns safety score and risk category for audit trails
- MCP-compatible for Claude Code and Cursor

GitHub: https://github.com/teodorofodocrispin-cmyk/TrustBoost-PII-Sanitizer
Health: https://api.trustboost.dev/health

## Compliance Coverage

GDPR (EU) | EU AI Act (Aug 2026) | HIPAA (USA) | LGPD (Brazil) | CCPA (California)
