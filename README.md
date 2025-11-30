# Aircraft Maintenance Assistant

End-to-end **Retrieval-Augmented Generation (RAG)** assistant for aircraft maintenance guidance.

You can ask operational / maintenance questions, for example:

- “How to check brakes in an aircraft?”
- “Explain A-check vs C-check.”
- “Hydraulic leak troubleshooting steps for landing gear.”

The system then:

1. Retrieves relevant procedures from local aircraft manuals (PDF / PPTX).
2. Optionally enriches answers with **Tavily** web search.
3. Synthesizes a structured, safety-aware answer using **Groq LLM (`compound-beta`)**.
4. Keeps lightweight **conversation memory** per session.

> ⚠️ **Important**  
> This project is for **learning / demo** only.  
> It does **not** authorize real maintenance and must never replace official AMM / regulatory procedures.

---

## 1. Tech Stack

### Backend

- Python 3.11
- **FastAPI** + **Uvicorn**
- **sentence-transformers**  
  - Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim embeddings)
- **FAISS (CPU)** – in-memory vector index
- **LangChain**
  - Used mainly for text chunking via `RecursiveCharacterTextSplitter`
- **pypdf** – PDF parsing
- **python-pptx** – PPTX parsing
- **Tavily** Web Search API
- **Groq** Python SDK  
  - Model: `compound-beta` for chat completions
- Simple JSON-file **memory** store for conversations

### Frontend

- Static assets served by FastAPI:
  - `web/index.html` – chat UI
  - `web/assets/style.css` – layout & theming
  - `web/assets/app.js` – chat logic (calls `/api/chat`)
- Lightweight Markdown renderer (via CDN) to format the LLM answer

---

## 2. Repository Layout

```text
aircraft-maintenance-assistant/
├─ 1 Dataset/             # NOT in Git – local manuals (PDF, PPTX, etc.)
├─ app/
│  ├─ __init__.py
│  ├─ config.py           # paths, model names, API keys
│  ├─ ingest.py           # offline index building
│  ├─ retriever.py        # FAISS + embedding pipeline
│  ├─ llm.py              # Groq LLM client & prompting
│  ├─ websearch.py        # Tavily integration
│  ├─ memory.py           # simple per-session JSON memory
│  ├─ safety.py           # guardrails & disclaimers
│  └─ server.py           # FastAPI app (HTTP API + static UI)
├─ web/
│  ├─ index.html
│  └─ assets/
│     ├─ app.js
│     └─ style.css
├─ .env                   # local env vars (ignored in git)
├─ .gitignore             # ignores .env, virtualenv, dataset, index, etc.
└─ requirements.txt

3. RAG Pipeline Design
3.1 Documents & Formats

All manuals live under 1 Dataset/ at the repo root (not committed to Git).

Supported formats:

*.pdf – AMM, AOM, training manuals, regulatory docs

*.pptx – training slides, courseware

The folder 1 Dataset/ is ignored in .gitignore so you can keep large manuals locally.

3.2 Parsing & Normalization

PDFs (via pypdf):

Concatenate text from each page.

Strip control characters and very short lines.

PPTX (via python-pptx):

Read text from all shapes / text boxes.

Treat each slide as a “pseudo-page”.

Each file is converted into a list of (page_or_slide_id, raw_text) blocks.

3.3 Chunking Strategy

We use LangChain’s RecursiveCharacterTextSplitter with:

chunk_size = 1000 characters

chunk_overlap = 200 characters

separators = ["\n\n", "\n", " ", ""]

This produces overlapping chunks that try to respect paragraph boundaries.

Example from one index build:

~236,767 vector chunks

154 files

Embedding dimension: 384

3.4 Embeddings

Model: sentence-transformers/all-MiniLM-L6-v2

Embedding size: 384 dimensions

Embeddings are L2-normalized (unit length) → cosine similarity via inner product.

Stored in:

app/data/index/faiss.index – FAISS index

app/data/index/docstore.json – chunk metadata:

file_name

page_or_slide

chunk_id

text

(app/data/index/ is ignored in .gitignore so it never goes to GitHub.)

3.5 Vector Store (FAISS)

Index type: IndexFlatIP (inner product)

Combined with normalized vectors → cosine similarity.

Retrieval:

top_k = 5 chunks per query.

Results sorted by similarity score.

Internal retriever API (simplified):

retrieve(query: str) -> List[RetrievedChunk]


Each RetrievedChunk includes:

chunk text

file name

page / slide

similarity score

4. Web Search (Tavily)

File: app/websearch.py

Client: TavilyClient(api_key=TAVILY_API_KEY)

Used to fetch a small number of highly relevant web results.

The results are summarized into short “web blurbs”.

These blurbs are optionally appended to the LLM context as Web evidence.

If TAVILY_API_KEY is not set, web_blurbs() just returns an empty list → the app continues with pure local RAG.

5. LLM Orchestration (Groq)

File: app/llm.py

Client from Groq SDK:

from groq import Groq
client = Groq(api_key=GROQ_API_KEY)


Model: compound-beta (chat completion).

5.1 System Prompt

The system prompt tells the model to:

Use retrieved RAG chunks as primary ground truth.

Use Tavily evidence (if any) as secondary support.

Format answers in Markdown with sections such as:

## Short Overview

## Equipment / Tools / Location

## Step-by-Step Procedure

## Who Can Perform This

## Safety / Eligibility

## Sources

Keep bullet points tight (avoid giant paragraphs).

Always include a short “read-only guidance” disclaimer.

Never claim to authorize maintenance or sign-off.

5.2 Conversation Memory

File: app/memory.py

Simple per-session memory keyed by session_id.

Stores a rolling window of recent user / assistant messages.

Stored as small JSON files under app/data/memory/.

Memory messages are added to the LLM prompt so the conversation feels continuous.

6. Request Flow

For each chat request:

Frontend (web/assets/app.js)

Sends POST /api/chat with FormData:

message – user question

session_id – optional; created by server if missing

Backend (/api/chat in app/server.py)

Loads conversation memory (if session_id provided).

Runs RAG retrieval:

Encode query → embedding

Query FAISS → top_k chunks + scores

Optionally calls Tavily for web evidence.

Builds messages list (system + memory + context + user).

Calls Groq compound-beta for chat completion.

Updates memory with the new exchange.

Returns JSON:

{
  "answer": "<markdown>",
  "session_id": "abc123",
  "origin": "RAG" | "RAG+WEB",
  "sources": [
    {
      "file": "Air operations rules.pdf",
      "page": 1295,
      "score": 0.61
    }
  ],
  "retrieval": {
    "top_k": 5,
    "hits": 5,
    "best_similarity": 0.61
  }
}


Frontend

Shows the user message.

Renders the assistant answer as Markdown.

Shows a small warning bubble if an error occurs (HTTP 500, etc.).

7. Setup & Installation
7.1 Prerequisites

macOS / Linux / Windows

Python 3.11+

Groq API key

Tavily API key (optional but recommended)

7.2 Clone & Virtualenv
git clone https://github.com/<your-username>/aircraft-maintenance-assistant.git
cd aircraft-maintenance-assistant

python -m venv .venv
source .venv/bin/activate  # macOS / Linux
# .venv\Scripts\activate   # Windows PowerShell

7.3 Install Requirements
pip install --upgrade pip
pip install -r requirements.txt

7.4 Configure Environment

Create a .env file at the project root:

GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here


.env is already listed in .gitignore, so it will not be pushed to GitHub.

8. Add Manuals & Build the Index
8.1 Place Manuals

Copy your manuals (PDFs, PPTX, etc.) into:

1 Dataset/


The default path is configured in app/config.py.

8.2 Build FAISS Index
source .venv/bin/activate
python -m app.ingest


This creates / updates:

app/data/index/faiss.index

app/data/index/docstore.json

Both paths are ignored by Git so you can safely push the repo without large files.

9. Run the App Locally
source .venv/bin/activate
uvicorn app.server:app --host 127.0.0.1 --port 8000 --reload


Then open:

http://127.0.0.1:8000/

You’ll see the Aircraft Maintenance Assistant chat UI.

Try queries like:

“How to check brakes in aircraft?”

“Explain A-check vs C-check.”

“Hydraulic leak troubleshooting for landing gear.”

10. Safety Disclaimer

This assistant is for educational / demo use only.

It does not replace official Aircraft Maintenance Manuals.

It does not provide legal or regulatory approval.

Only licensed and authorized maintenance personnel may perform real-world tasks.