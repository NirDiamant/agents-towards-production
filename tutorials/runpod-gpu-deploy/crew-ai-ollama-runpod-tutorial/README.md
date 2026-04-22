![](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--runpod-gpu-deploy--crew-ai-ollama-runpod-tutorial--readme)

# CrewAI + Ollama on RunPod: Serverless AI Agents

## Overview

This repository demonstrates how to deploy an AI agent system on [RunPod](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--runpod-gpu-deploy--crew-ai-ollama-runpod-tutorial--readme&click=runpod-nirdiamant&target=https%3A%2F%2Fget.runpod.io%2Fnirdiamant&text=RunPod)'s serverless infrastructure. The sample application creates an API endpoint that generates blog posts on any topic through an AI agent workflow.

Key components:
- **CrewAI**: Framework for orchestrating role-playing AI agents
- **Ollama**: Tool for running open-source LLMs locally
- **RunPod**: Serverless GPU infrastructure for AI deployment

*Referenced from: [RunPod Worker Template](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--runpod-gpu-deploy--crew-ai-ollama-runpod-tutorial--readme&click=github-worker-template&target=https%3A%2F%2Fgithub.com%2Frunpod-workers%2Fworker-template&text=RunPod%20Worker%20Template)*

## RunPod Template

Get started immediately using our pre-configured RunPod template:

[<img src="https://img.shields.io/badge/RunPod-Deploy%20Now-blue?style=for-the-badge&logo=none" alt="Deploy on RunPod" width="200"/>](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--runpod-gpu-deploy--crew-ai-ollama-runpod-tutorial--readme&click=runpod-nirdiamant&target=https%3A%2F%2Fget.runpod.io%2Fnirdiamant&text=%3Cimg%20src%3D%22https%3A%2F%2Fimg.shields.io%2Fbadge%2FRunPod-Deploy%2520Now-blue%3Fstyle%3Dfor-the-badge%26logo%3Dnone%22%20alt%3D%22Deploy%20on%20RunPod%22%20width%3D%22200%22%2F%3E)

## How It Works

This application:
1. Exposes an API endpoint through RunPod
2. Accepts a topic as input
3. Uses CrewAI to manage an AI agent that:
   - Researches the topic (using a mock research tool in this example)
   - Writes a structured blog post
4. Returns the generated blog post as JSON

## Architecture

- **Handler Function**: Entry point that processes requests (handler.py)
- **Blog Writer Agent**: AI agent configured for content creation
- **Mock Research Tool**: Simulates research by providing predefined facts
- **Docker Container**: Packages everything with Ollama for serverless deployment

## Getting Started

### Deployment to RunPod

#### Option 1: Use RunPod Template (Recommended)

1. Click the "Deploy on RunPod" button above
2. Configure your endpoint settings
3. Deploy and start using immediately

#### Option 2: Build and Deploy Custom Image

1. Build the Docker image:
   ```bash
   docker build -t yourusername/crew-ai-ollama:latest . --platform linux/amd64
   docker push yourusername/crew-ai-ollama:latest
   ```

2. Create a new Serverless Endpoint on RunPod
3. Select "Docker Image" as the source
4. Enter your image URL
5. Configure hardware settings (recommended: GPU with 24GB+ VRAM)
6. Set worker count (min: 0, max: based on expected traffic)
7. Deploy your endpoint

## Usage

### API Endpoint

Once deployed, your RunPod endpoint will provide a URL in this format:
```
https://api.runpod.ai/v2/[ENDPOINT_ID]/run
```

### Example Request

```bash
curl --request POST \
     --url https://api.runpod.ai/v2/[ENDPOINT_ID]/run \
     --header "accept: application/json" \
     --header "authorization: [YOUR_API_KEY]" \
     --header "content-type: application/json" \
     --data '
{
  "input": {
    "topic": "artificial intelligence"
  }
}
'
```

### Example Response

```json
{
  "delayTime": 14836,
  "executionTime": 10799,
  "id": "4c04615b-540f-4d82-917d-4eb4256acd96-u1",
  "output": {
    "blog_post": "Title: The Future of Technology: A Promising Horizon\n\nIntroduction:\nTechnology has been a driving force behind human progress, constantly evolving to meet the challenges of our time. In recent years, the pace of technological advancements has accelerated, and we stand on the precipice of an exciting new era. This blog post explores the current state of technology, highlights its most promising trends, and looks forward to what's in store for the future.\n\nMain Points:\n1. The Unrelenting Importance of Technology: As per recent research, 82% of industry leaders consider technology a pivotal area of focus, demonstrating its significance in shaping our world. From healthcare and education to communication and entertainment, technology continues to transform our daily lives.\n2. Rising Research Investments: Last year alone, spending on technology-related research grew by an impressive 34%. This surge in investment highlights the growing belief that technological innovation will be a primary catalyst for economic growth and societal progress.\n3. Soaring Consumer Interest: Consumer interest in technology has soared since 2022, with a staggering 56% increase recorded. This rapid growth is a testament to the increasing role of technology in our lives and its ability to address the evolving needs and desires of individuals worldwide.\n4. A Promising Horizon: Experts predict that the next five years will bring significant advancements in technology. From artificial intelligence and quantum computing to breakthroughs in biotechnology, the future promises a world of endless possibilities and new frontiers to explore.\n\nConclusion:\nThe future of technology is undoubtedly bright, with innovation driving us towards a more connected, efficient, and prosperous society. As we forge ahead into this exciting new era, it's crucial that we continue to invest in research, foster collaboration, and embrace the transformative potential of technology. Our collective commitment to harnessing its power will determine the extent to which we can leverage technology to overcome global challenges and shape a better tomorrow for all.\n\nCall to Action:\nJoin the conversation on social media using #FutureOfTech and share your thoughts about how technology is changing our world. Let's engage in a dialogue that fosters understanding, inspiration, and collective action towards an even brighter future.",
    "status": "success"
  },
  "status": "COMPLETED",
  "workerId": "fy17taoa4pyz2c"
}
```

## Key Files

### handler.py

The main entry point for processing requests:

```python
import runpod
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
import os

# Configure Ollama LLM
llm = LLM(model="ollama/openhermes", base_url="http://localhost:11434")

# Create a pseudo-research tool that returns fake information
@tool("Research Tool")
def fake_research(topic: str) -> str:
    """
    Pretends to search for information about a topic. 
    Will always return some fake pre-defined content.
    """
    # ... returns fake research data
    
# Create blog writer agent
blog_writer = Agent(
    role="Blog Writer",
    goal="Write engaging and informative blog posts on various topics",
    backstory="You are a professional blog writer...",
    tools=[fake_research],
    verbose=True,
    llm=llm
)

def create_blog_post(topic):
    """Creates a blog post on the given topic using CrewAI"""
    # ... creates and executes the task

def handler(job):
    """Handler function that will be used to process jobs."""
    job_input = job["input"]
    topic = job_input.get("topic", "technology")
    
    try:
        blog_post = create_blog_post(topic)
        return {
            "status": "success",
            "blog_post": blog_post
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

runpod.serverless.start({"handler": handler})
```

### Dockerfile

Contains the configuration for creating a containerized version of the application:

```Dockerfile
FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04

# Install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip && \
    pip install uv && \
    uv pip install --upgrade -r /requirements.txt --no-cache-dir && \
    uv pip install "langchain-community>=0.0.34" --no-cache-dir

# Download model during build
RUN ollama serve > /dev/null 2>&1 & \
    sleep 25 && \
    ollama pull openhermes && \
    sleep 10 && \
    pkill ollama

# Startup script
CMD ["/start.sh"]
```

## Performance Considerations

- The first request may experience cold-start latency as the container initializes
- Pre-loading the Ollama model in the Docker image significantly improves response time
- Response times typically range from 5-15 seconds depending on the complexity of the topic

## Extending This Project

This template can be extended in several ways:
- Replace the mock research tool with real web search functionality
- Add more specialized agents for different aspects of content creation
- Implement more complex workflows with multiple agents collaborating
- Fine-tune the LLM for your specific use case

## Acknowledgements

- [CrewAI](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--runpod-gpu-deploy--crew-ai-ollama-runpod-tutorial--readme&click=github-crewai&target=https%3A%2F%2Fgithub.com%2FcrewAIInc%2FcrewAI&text=CrewAI)
- [Ollama](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--runpod-gpu-deploy--crew-ai-ollama-runpod-tutorial--readme&click=github-ollama&target=https%3A%2F%2Fgithub.com%2Follama%2Follama&text=Ollama)
- [RunPod](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--runpod-gpu-deploy--crew-ai-ollama-runpod-tutorial--readme&click=runpod-nirdiamant&target=https%3A%2F%2Fget.runpod.io%2Fnirdiamant&text=RunPod)
- [RunPod Worker Template](https://europe-west1-atp-views-tracker.cloudfunctions.net/working-analytics?notebook=tutorials--runpod-gpu-deploy--crew-ai-ollama-runpod-tutorial--readme&click=github-worker-template&target=https%3A%2F%2Fgithub.com%2Frunpod-workers%2Fworker-template&text=RunPod%20Worker%20Template)