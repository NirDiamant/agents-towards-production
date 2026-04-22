![](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--agent-memory-with-redis--readme)

# 🧠 Agent Memory with Redis

Build a **memory-enabled AI agent** that remembers user preferences and learns from conversations using Redis and LangGraph.

## 🎯 What You'll Learn

The goal of this tutorial is to empower you with a **horizontal concept** that you can apply to your own agent use cases.

- **Dual-Memory Architecture**: Implement short-term (conversation state) and long-term (persistent knowledge) memory
- **Semantic Search**: Use RedisVL for semantic memory retrieval with embeddings
- **Memory Types**: Understand differences between episodic (user experiences) vs semantic (general knowledge) memory patterns
- **Production Patterns**: Tool-based memory management and conversation summarization
- **LangGraph Integration**: Build complete workflows with Redis checkpointers for state persistence

## 📓 Tutorial

[Agent Memory Tutorial Notebook](agent_memory_tutorial.ipynb)

## 🚀 Run in Google Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NirDiamant/agents-towards-production/blob/main/tutorials/agent-memory-with-redis/agent_memory_tutorial.ipynb)

## �� Requirements

- **OpenAI API Key** (with billing enabled)
- **Redis** optionally installed in Colab, or use [Redis Cloud](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--agent-memory-with-redis--readme&click=redis-try-free&target=https%3A%2F%2Fredis.io%2Ftry-free%2F%3Futm_source%3Dnir%26utm_medium%3Dcpa%26utm_campaign%3D2025-05-ai_in_production-influencer-nir%26utm_content%3Dsd-software_download-7013z000001WaRY&text=Redis%20Cloud)

## 🎓 What You'll Build

A travel agent that:
- Remembers user preferences across conversations
- Stores long term memories ("I prefer Delta airlines") 
- Provides personalized recommendations based on past interactions
- Manages conversation context automatically

**Total Tutorial Time**: ~30-45 minutes  
**Difficulty**: Intermediate (Python, LangGraph, Tool calling, other basic AI concepts)
