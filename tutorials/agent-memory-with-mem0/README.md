![](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--agent-memory-with-mem0--readme)

# Persistent Memory for AI Agents with Mem0

Build intelligent AI agents with persistent, evolving memory using Mem0's hybrid retrieval (semantic, keyword and entity matching). Learn to implement adaptive memory systems that continuously learn from user interactions and self-improve over time.

## **🎯 What You'll Learn**

- **Storing long-term knowledge** using a vector database for semantic recall
- **Boosting recall with entities** that Mem0 extracts from each memory (papers, authors, models)
- **Combining semantic, keyword (BM25) and entity signals** to answer richer research queries
- **Teaching agents user-specific preferences** and using that context in future sessions
- **Reading Mem0's score breakdown** to see why a memory was retrieved

## **📓 Tutorial**

[Mem0 Tutorial Notebook](mem0_tutorial.ipynb)

## **🚀 Run in Google Colab**

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NirDiamant/agents-towards-production/blob/main/tutorials/agent-memory-with-mem0/mem0_tutorial.ipynb)

## **Requirements**

- **[Mem0](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--agent-memory-with-mem0--readme&click=mem0-nir&target=https%3A%2F%2Fmem0.dev%2Fgithub%2Fnir&text=Mem0)** (Open Source)
- **OpenAI API Key**: For LLM reasoning and embeddings
- **Qdrant Cloud or another vector store supported by Mem0** (optional): without it the notebook uses a local Qdrant folder
- **mem0 2.x** (`mem0ai[nlp]>=2.2`): mem0 2.0 removed the external graph store (Neo4j) from the open-source package. Earlier versions of this tutorial used Neo4j; that version needs `mem0ai<2`.

## **🎓 What You'll Build**

**Personal AI Research Assistant** that:

- Maintains intelligent memory that automatically extracts and stores research interests
- Links memories to the papers, authors and concepts they mention, and boosts them when a question names the same entities
- Adapts to user preferences through self-improving memory capabilities
- Provides contextual assistance using hybrid memory retrieval
- Learns and evolves from each research conversation