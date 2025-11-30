from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil, uuid, urllib.parse as _uq, time, random

from .config import APP_NAME, WEB_DIR, INDEX_DIR, DATASET_DIR
from .safety import classify_policy
from .retriever import search, build_index
from .llm import chat
from .memory import append_turn, load_history
from .websearch import web_blurbs

app = FastAPI(title=APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/assets", StaticFiles(directory=str(WEB_DIR / "assets")), name="assets")
app.mount("/docs", StaticFiles(directory=str(DATASET_DIR)), name="docs")

@app.get("/", response_class=HTMLResponse)
def home():
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    dst = DATASET_DIR / file.filename
    with open(dst, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"status": "ok", "saved": str(dst)}

@app.post("/api/reindex")
def reindex():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    stats = build_index()
    return {"status": "ok", "stats": stats}

@app.post("/api/chat")
async def api_chat(message: str = Form(...), session_id: str = Form(None)):
    t0 = time.perf_counter()
    session_id = session_id or str(uuid.uuid4())
    label = classify_policy(message)

    # Retrieval
    t = time.perf_counter()
    passages = search(message, k=5)
    t_retrieval = time.perf_counter() - t

    # Build context and links
    link_items, ctx_blocks = [], []
    for p in passages:
        meta = p["meta"]
        fname = Path(meta.get("source", "")).name or "document"
        page = int(meta.get("page", 1))
        href = "/docs/" + _uq.quote(fname) + f"#page={page}"
        link_items.append({"type": "pdf", "name": fname, "page": page, "href": href})
        dtype = meta.get("doc_type", ".pdf")
        ctx_blocks.append(f"[Source: {fname} • {dtype} • p.{page}]\n" + p["text"][:1200])

    # Fallback to web if needed
    web_used, t_web = False, 0.0
    if len(passages) < 2:
        web_used = True
        t = time.perf_counter()
        web = web_blurbs(message, k=3)
        t_web = time.perf_counter() - t
        for r in web:
            link_items.append({"type": "web", "name": r["title"], "href": r["url"], "page": None})
            ctx_blocks.append(f"[Web: {r['title']} | {r['url']}]\n" + r["summary"][:800])

    # Determine origin flag
    origin = "RAG" if passages else "LLM"
    if web_used and passages:
        origin = "RAG+LLM"

    # System prompt
    system = """You are an aircraft maintenance assistant. Provide READ-ONLY guidance with strict citations and never authorize maintenance or sign-offs.

Answer in Markdown using the exact sections below, in this order, and keep prose concise:

## Short Overview
3–4 short sentences summarizing the situation; avoid long paragraphs or excess commentary.

## Equipment / Tools / Location
Use a brief bullet list or compact table for required gear, tools, and location details.

## Step-by-Step Procedure
Use a numbered list, keeping each step 1–3 short sentences; prioritize clarity and brevity.

## Who Can Perform This
List qualified roles in a short bullet list.

## Safety / Eligibility
Include concise cautions and eligibility notes; keep this section read-only.

## Sources
Provide a short bullet list naming each document and page number only.

Avoid cross-references and overly long paragraphs; prefer short bullets and clear headings."""

    # Chat history
    history = load_history(session_id, limit=24)
    msgs = [{"role": "system", "content": system}]
    msgs += history
    msgs.append({
        "role": "user",
        "content": message + "\n\nContext:\n" + "\n\n---\n\n".join(ctx_blocks[:6])
    })

    # Call LLM
    try:
        t = time.perf_counter()
        answer, usage = chat(msgs)
        t_llm = time.perf_counter() - t
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "error": "LLM request failed.",
                "details": str(exc),
                "session_id": session_id,
            },
        )
    total = time.perf_counter() - t0

    # Build metrics
    runtime = {
        "total": round(total, 3),
        "retrieval": round(t_retrieval, 3),
        "web": round(t_web, 3),
        "llm": round(t_llm, 3),
        "hits": len(passages),
        "fallback_used": web_used
    }
    metrics = {"origin": origin, "runtime": runtime}

    # Save to memory
    append_turn(session_id, "user", message, {"label": label})
    append_turn(session_id, "assistant", answer, {"metrics": metrics, "usage": usage})

    return {
        "session_id": session_id,
        "label": label,
        "answer": answer,
        "links": link_items,
        "metrics": metrics,
        "usage": usage
    }
