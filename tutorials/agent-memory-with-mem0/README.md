![](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--agent-memory-with-mem0--readme)

# Persistent Memory for AI Agents with Mem0

Build intelligent AI agents with persistent, evolving memory using Mem0's hybrid storage architecture. Learn to implement adaptive memory systems that continuously learn from user interactions and self-improve over time.

## **🎯 What You'll Learn**

- **Storing long-term knowledge** using a vector database for semantic recall
- **Mapping concepts into a knowledge graph** using Mem0’s graph memory capabilities
- **Blending structured and unstructured memory** to answer richer research queries
- **Teaching agents user-specific preferences** and using that context in future sessions
- **Retrieving the right information** by combining embeddings and graph traversal

## **📓 Tutorial**

[Mem0 Tutorial Notebook](mem0_tutorial.ipynb)

## **🚀 Run in Google Colab**

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NirDiamant/agents-towards-production/blob/main/tutorials/agent-memory-with-mem0/mem0_tutorial.ipynb)

## **Requirements**

- **[Mem0](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--agent-memory-with-mem0--readme&click=mem0-nir&target=https%3A%2F%2Fmem0.dev%2Fgithub%2Fnir&text=Mem0)** (Open Source)
- **OpenAI API Key**: For LLM reasoning and embeddings
- **Qdrant or another vector store supported by Mem0**: Vector database for semantic search
- **Neo4j or another graph database supported by Mem0**: Graph database for relationship mapping

## **🎓 What You'll Build**

**Personal AI Research Assistant** that:

- Maintains intelligent memory that automatically extracts and stores research interests
- Maps knowledge relationships between papers, authors, and concepts using graph storage
- Adapts to user preferences through self-improving memory capabilities
- Provides contextual assistance using hybrid memory retrieval
- Learns and evolves from each research conversation