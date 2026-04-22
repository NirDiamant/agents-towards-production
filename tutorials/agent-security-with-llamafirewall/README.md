![](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--agent-security-with-llamafirewall--readme)

# LlamaFirewall For AI Agents Security Tutorial

## Overview

Protect your AI agents from security threats using **LlamaFirewall** - an open-source security framework that provides comprehensive guardrails for production AI systems. Learn to implement input validation, output monitoring, and tool security to build secure, production-ready agents.

<div align="center">
<img src="assets/tools-security.png" alt="LlamaFirewall Tools Security Interface" width="600"/>
</div>

## What You'll Learn

- **Input Security**: Protect against prompt injection and harmful content
- **Output Validation**: Ensure agent responses align with intended behavior
- **Tool Security**: Prevent unauthorized tool usage and resource abuse
- **Real-Time Monitoring**: Track security events with comprehensive logging
- **Production Deployment**: Implement security measures in real-world applications

## Tutorials

### **[Hello Llama: hello-llama.ipynb](./hello-llama.ipynb)**
Basic message scanning to detect and block potentially harmful content.

### **[Input Guardrail: input-guardrail.ipynb](./input-guardrail.ipynb)**
Validate user inputs to protect against malicious prompts and injection attacks.

### **[Output Guardrail: output-guardrail.ipynb](./output-guardrail.ipynb)**
Validate AI agent responses to ensure they align with intended behavior.

### **[Tools Security: tools-security.ipynb](./tools-security.ipynb)**
Comprehensive security for AI agent tools with input validation and access control.

## Quick Start

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Get API keys**: OpenAI API key + Together AI key for alignment checks
3. **Set up HuggingFace**: Request access to Llama Prompt Guard 2 model
4. **Configure**: Run `llamafirewall configure` to set up models and API keys

## Authors
Created by [Matan Kotick](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--agent-security-with-llamafirewall--readme&click=linkedin-matan-kotick-664735252&target=https%3A%2F%2Fwww.linkedin.com%2Fin%2Fmatan-kotick-664735252&text=Matan%20Kotick) and [Amit Ziv](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--agent-security-with-llamafirewall--readme&click=linkedin-amit-ziv-49690b120&target=https%3A%2F%2Fwww.linkedin.com%2Fin%2Famit-ziv-49690b120&text=Amit%20Ziv).