"""Khushi AI — FastAPI server.

Exposes:
  GET  /                     -> built-in chat UI (static/index.html)
  GET  /health               -> readiness + which model is loaded
  POST /chat                 -> {"reply": "...", "sources": [...]}   (JSON)
  POST /chat/stream          -> streamed plain-text reply            (for the UI)
  POST /v1/chat/completions  -> OpenAI-compatible endpoint (any frontend)
  GET  /v1/models            -> OpenAI-compatible model list
  POST /research             -> standalone research tool (sources + context), for agents
"""
import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import config
from app.llm import KhushiLLM, ensure_model
from app.persona import build_messages
from app.search import format_context, web_search

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="Khushi AI", version="1.0.0")

# Open CORS so any frontend (website, app, another service) can call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_llm = None  # lazily loaded on first request


def get_llm():
    global _llm
    if _llm is None:
        path = ensure_model(config.MODEL_REPO, config.MODEL_FILE, config.MODEL_CACHE)
        _llm = KhushiLLM(path, n_ctx=config.N_CTX, n_threads=config.N_THREADS, n_batch=config.N_BATCH)
    return _llm


# ------------------------------- schemas -----------------------------------
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []
    use_web: bool | None = None


class OpenAIChatRequest(BaseModel):
    model: str = "khushi"
    messages: list[Message]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False


class ResearchRequest(BaseModel):
    query: str
    max_results: int | None = None


# ------------------------------ helpers ------------------------------------
async def _research(query, use_web):
    """Return (context_block, sources) — empty when research is off or fails."""
    if not use_web or not config.ENABLE_WEB:
        return None, []
    results = await web_search(query, config.WEB_MAX_RESULTS)
    if not results:
        return None, []
    sources = [{"title": r["title"], "url": r["url"]} for r in results]
    return format_context(results), sources


def _gen_kwargs(temperature=None, max_tokens=None):
    return {
        "temperature": config.TEMPERATURE if temperature is None else temperature,
        "max_tokens": config.MAX_TOKENS if max_tokens is None else max_tokens,
        "top_p": config.TOP_P,
    }


# ------------------------------- routes ------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_repo": config.MODEL_REPO,
        "model_loaded": _llm is not None,
        "web_research": config.ENABLE_WEB,
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    use_web = config.ENABLE_WEB if req.use_web is None else req.use_web
    context, sources = await _research(req.message, use_web)
    messages = build_messages([m.model_dump() for m in req.history], req.message, context)
    reply = get_llm().complete(messages, **_gen_kwargs())
    return {"reply": reply, "sources": sources}


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    use_web = config.ENABLE_WEB if req.use_web is None else req.use_web
    context, sources = await _research(req.message, use_web)
    messages = build_messages([m.model_dump() for m in req.history], req.message, context)
    llm = get_llm()

    def gen():
        # First line = sources (JSON), then "---", then the streamed answer.
        import json

        yield json.dumps({"sources": sources}) + "\n---\n"
        for piece in llm.stream(messages, **_gen_kwargs()):
            yield piece

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")


@app.post("/v1/chat/completions")
async def openai_chat(req: OpenAIChatRequest):
    """OpenAI-compatible endpoint so ANY frontend can plug in."""
    # Optionally allow the caller to force research via the system message.
    context, sources = None, []
    last_user = next((m.content for m in reversed(req.messages) if m.role == "user"), "")
    if config.ENABLE_WEB and last_user:
        context, sources = await _research(last_user, True)

    msgs = [m.model_dump() for m in req.messages]
    if context:
        msgs.append({"role": "system", "content": f"Web research context:\n{context}"})

    llm = get_llm()
    kwargs = _gen_kwargs(req.temperature, req.max_tokens)

    if req.stream:
        def gen():
            for piece in llm.stream(msgs, **kwargs):
                yield piece

        return StreamingResponse(gen(), media_type="text/event-stream")

    reply = llm.complete(msgs, **kwargs)
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": reply}, "finish_reason": "stop"}
        ],
        "sources": sources,
    }


@app.post("/research")
async def research(req: ResearchRequest):
    """Standalone research tool for agents.

    Returns raw sources + a ready-to-paste context block. No LLM call is made,
    so an external agent can use this purely as a retrieval step.
    """
    k = req.max_results or config.WEB_MAX_RESULTS
    results = await web_search(req.query, k)
    sources = [{"title": r["title"], "url": r["url"]} for r in results]
    return {
        "query": req.query,
        "results": results,
        "sources": sources,
        "context": format_context(results),
    }


@app.get("/v1/models")
def models():
    return {
        "object": "list",
        "data": [{"id": "khushi", "object": "model", "owned_by": "local"}],
    }


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
