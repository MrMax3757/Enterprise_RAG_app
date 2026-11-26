# Enterprise Agentic RAG

A production-oriented **Agentic Retrieval-Augmented Generation (RAG)** system built with **LangGraph**, **FastAPI**, **Streamlit**, **Qdrant**, **FlashRank**, **NVIDIA NeMo Guardrails**, **Portkey / Groq**, and **Pydantic Logfire**.

---

## Architecture

Every incoming query passes through a two-stage pipeline:

1. **NeMo Guardrails Gate (`app/guardrails/`)**: Filters off-topic queries, jailbreak attempts, greetings, farewells, and capability inquiries using Colang rules before invoking the RAG pipeline.
2. **LangGraph Agent (`app/agents/`)**:
   - **Planner (`planner_node`)**: Inspects conversation history and classifies whether the query is `CONVERSATIONAL` (answered from `MemorySaver` thread history) or technical (rewritten into a search query).
   - **Retriever (`retrieve_node`)**: Queries Qdrant (`search_enterprise_knowledge`) for top 15 candidate chunks, then reranks locally using FlashRank (`rerank_documents`) to keep the top 5 most relevant chunks.
   - **Responder (`generate_node`)**: Synthesizes the final answer via Portkey Gateway (with automatic fallback to direct Groq when `PORTKEY_API_KEY` is not configured).

---

## Project Structure

```text
Enterprise_RAG_app/
├── app/
│   ├── agents/
│   │   ├── nodes/
│   │   │   ├── planner.py          # Intent classification & query refinement
│   │   │   ├── retriever.py        # Qdrant search + FlashRank reranking
│   │   │   └── responder.py        # Answer synthesis + cache status extraction
│   │   ├── graph.py                # LangGraph StateGraph + MemorySaver
│   │   └── state.py                # AgentState TypedDict
│   ├── gateway/
│   │   ├── __init__.py
│   │   └── client.py               # Portkey client + direct Groq fallback
│   ├── guardrails/
│   │   ├── __init__.py
│   │   ├── colang_rules.py         # Colang intents, flows, and indicators
│   │   └── rails.py                # LLMRails singleton, initialize_rails(), guard()
│   ├── ingestion/
│   │   ├── chunking/splitter.py    # Paragraph-based text chunker
│   │   ├── loaders/                # PDF, HTML, DOCX/PPTX, and TXT loaders
│   │   └── processor.py            # Batch ingestion pipeline to Qdrant
│   ├── services/retrieval/
│   │   ├── embeddings.py           # Gemini embeddings with SentenceTransformers fallback
│   │   ├── qdrant_service.py       # Qdrant query_points search
│   │   └── ranking_service.py      # FlashRank local cross-encoder reranker
│   ├── config.py                   # Environment-backed Settings
│   └── main.py                     # FastAPI application (/, /graph, /query)
├── ui/
│   ├── app.py                      # Streamlit chat UI
│   └── st_cloud_ui.py              # Streamlit Cloud variant
├── DATA/
│   ├── DOCS/                       # System guides & architecture docs
│   └── true_data/                  # Source documents for ingestion
├── evals/                          # RAGAS / DeepEval evaluation scripts
├── Dockerfile                      # Unified FastAPI + Streamlit container
├── start.sh                        # Container entrypoint script
├── render.yaml                     # Render Blueprint deployment config
├── .env.example                    # Environment variable template
└── requirements.txt
```

---

## Local Setup & Running

### 1. Create & Activate Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```env
GROQ_API_KEY="gsk_..."
GROQ_MODEL="qwen/qwen3.8-27b"
QDRANT_API_KEY="eyJ..."
QDRANT_CLUSTER_ENDPOINT="https://your-cluster.cloud.qdrant.io"
QDRANT_COLLECTION="Enterprise_RAG"
```

### 3. Ingest Documents (Optional if Qdrant is already populated)

```powershell
python -m app.ingestion.processor DATA/true_data true
```

Add `--wipe` to recreate the Qdrant collection before ingesting.

### 4. Start Backend & Frontend

**Terminal 1 (FastAPI Backend):**
```powershell
.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (Streamlit UI):**
```powershell
.venv\Scripts\activate
streamlit run ui/app.py
```

Open `http://localhost:8501` in your browser. FastAPI docs are available at `http://127.0.0.1:8000/docs`.

---

## Docker & Cloud Deployment (Render)

The repository includes [`Dockerfile`](Dockerfile), [`start.sh`](start.sh), and [`render.yaml`](render.yaml) to run both FastAPI and Streamlit in a single container.

### Deploy on Render (Free Tier)

1. Push this repository to GitHub (`git push -u origin main`).
2. On [render.com](https://render.com), click **New +** → **Web Service** and connect your repository.
3. Select **Docker** as the runtime (auto-detected from `Dockerfile`).
4. Add your environment variables (`GROQ_API_KEY`, `QDRANT_API_KEY`, `QDRANT_CLUSTER_ENDPOINT`, etc.) in the Render dashboard.
5. Click **Create Web Service**.
