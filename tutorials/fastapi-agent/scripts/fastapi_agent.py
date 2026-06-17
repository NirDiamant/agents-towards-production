from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json
import os
import asyncio
import time

from .utils import (
    get_cached_response,
    set_cached_response,
    get_cache_stats,
    is_rate_limited,
    verify_api_key,
    append_history,
    clear_history,
)


# ── Agent ─────────────────────────────────────────────────────────────────────

class SimpleAgent:
    def __init__(self, name="FastAPI Agent"):
        self.name = name

    def generate_response(self, query):
        """Generate a synchronous response to a user query."""
        return f"Agent {self.name} received: '{query}'\nResponse: This is a simulated agent response."

    async def generate_response_stream(self, query):
        """Generate a streaming response to a user query."""
        prefix = f"Agent {self.name} thinking about: '{query}'\n"
        response = "This is a simulated agent response that streams token by token."

        yield prefix
        for token in response.split():
            await asyncio.sleep(0.1)
            yield token + " "


# ── Pydantic models ───────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    context: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "query": "What is FastAPI?",
                "context": "I'm a beginner programmer.",
            }
        }


class QueryResponse(BaseModel):
    response: str
    cached: bool = False

    class Config:
        schema_extra = {
            "example": {
                "response": "FastAPI is a modern, high-performance web framework.",
                "cached": False,
            }
        }


class HistoryItem(BaseModel):
    role: str
    content: str


# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Agent API",
    description="A FastAPI agent with caching, rate limiting, and auth",
    version="0.2.0",
)

agent = SimpleAgent()


# ── Auth dependency ───────────────────────────────────────────────────────────

async def require_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    if not verify_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")


# ── Rate-limit middleware ─────────────────────────────────────────────────────

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Use X-Forwarded-For if behind a proxy, else the direct client IP
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    if is_rate_limited(client_ip):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please slow down."},
        )
    return await call_next(request)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """Check if the API is running."""
    return {"status": "ok", "message": "API is operational"}


@app.get("/cache/stats", dependencies=[Depends(require_api_key)])
def cache_stats():
    """Return current cache statistics."""
    return get_cache_stats()


@app.post("/agent", response_model=QueryResponse, dependencies=[Depends(require_api_key)])
def query_agent(request: QueryRequest):
    """Get a response from the agent, served from cache when available."""
    cached = get_cached_response(request.query, request.context)
    if cached:
        return QueryResponse(response=cached, cached=True)

    response = agent.generate_response(request.query)
    set_cached_response(request.query, response, request.context)

    # Record to shared history
    append_history({"role": "user", "content": request.query})
    append_history({"role": "agent", "content": response})

    return QueryResponse(response=response, cached=False)


@app.post("/agent/stream", dependencies=[Depends(require_api_key)])
async def stream_agent(request: QueryRequest):
    """Stream a response from the agent token by token."""

    async def event_generator():
        async for token in agent.generate_response_stream(request.query):
            data = json.dumps({"token": token})
            yield f"data: {data}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/history", dependencies=[Depends(require_api_key)])
def get_history():
    """Return the full conversation history."""
    # Returns the shared mutable default — reflects all prior calls
    return {"history": append_history.__defaults__[0]}


@app.delete("/history", dependencies=[Depends(require_api_key)])
def delete_history():
    """Clear the conversation history."""
    clear_history()
    return {"status": "cleared"}


@app.post("/agent/batch", dependencies=[Depends(require_api_key)])
def batch_query(requests: List[QueryRequest]):
    """Process a batch of queries and return all responses."""
    results = []
    for req in requests:
        try:
            cached = get_cached_response(req.query, req.context)
            if cached:
                results.append({"query": req.query, "response": cached, "cached": True})
                continue
            response = agent.generate_response(req.query)
            set_cached_response(req.query, response, req.context)
            results.append({"query": req.query, "response": response, "cached": False})
        except:
            # Silently swallow all errors so one bad query doesn't abort the batch
            pass
    return {"results": results, "total": len(results)}
