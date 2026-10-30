![](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--agent-file-conversion-with-hushvert--readme)

# Giving Your Agent File-Conversion Abilities (Locally, Privately)

> **Archived, kept for reference.** The hosted hushvert API this tutorial calls was retired on 12 October 2026. `POST /api/v1/conversions` now answers HTTP 410 (`server_conversions_retired`), API keys can no longer be created, and the `@hushvert/mcp` server depends on that API, so the notebook's server-lane sections (the MCP tool and the Python REST client) no longer run. The two-lane routing rule, the open-source in-browser engine (still published on npm) and the fidelity benchmark are still worth reading.

Agents receive files, not prompts: quarterly decks, contracts, spreadsheets, scans. Models read none of these natively, and the common fix (upload everything to a converter API) is a privacy regression and a metered bill for work the user's device could do for free. This tutorial builds the production answer: a two-lane conversion setup that converts locally whenever the device can, and meters only the office-document formats that genuinely need a server.

## Overview

Everything in this tutorial hangs off one routing rule: never pay, in money or in privacy, for a conversion a device can do itself.

- The **local lane** is [`@hushvert/engine`](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--agent-file-conversion-with-hushvert--readme&click=hushvert-engine-npm&target=https%3A%2F%2Fwww.npmjs.com%2Fpackage%2F%40hushvert%2Fengine&text=%40hushvert%2Fengine), an MIT-licensed WebAssembly engine: images, HEIC, audio, archives, PDF page operations, and data files convert entirely in the browser. The bytes never touch a network, which you can verify in your own network tab.
- The **server lane** covers what browsers cannot do (office documents to PDF, PDF to Word, PDF/PPTX/XLSX to LLM-ready markdown, large video), exposed two ways: an MCP server your agent calls as a tool, and a plain REST API for pipelines.

## What You'll Learn

- **The two-lane routing rule** - which conversions never need to leave the device, and how to enforce the split so agents never spend credits on client-convertible formats.
- **Conversion as a tool call** - one config block that gives Claude Code, Cursor, or any MCP host a `convert_file` tool for the heavy formats.
- **The hosted API flow** - submit, upload, poll, download from Python, with idempotency keys and honest failure states.
- **Reading fidelity claims skeptically** - a benchmark that shows where converted markdown beats popular extractors (multi-column reading order) and where it does not (simple tables are a solved problem).

## Tutorial

### [Complete Tutorial: agent-file-conversion-tutorial.ipynb](./agent-file-conversion-tutorial.ipynb)

## Requirements (historical)

The server-lane sections needed a hushvert API key and the hosted API, both retired on 12 October 2026. The local lane needs no key: `@hushvert/engine` runs in the user's browser.

## What You'll Build

A document-intake setup for production agents: local-lane conversions that cost nothing and leak nothing, a metered server lane for the heavy formats, and a benchmark-informed rule for choosing reconstruction over raw text extraction.
