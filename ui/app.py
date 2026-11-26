import os
import time
import uuid
import requests
import streamlit as st
import logfire
from dotenv import load_dotenv

# --- LOAD ENVIRONMENT ---
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path=env_path)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

# --- LOGFIRE OBSERVABILITY ---
try:
    token = os.getenv("LOGFIRE_TOKEN")
    logfire.configure(token=token, send_to_logfire="if-token-present")
    LOGFIRE_STATUS = "Connected & Tracing"
    LOGFIRE_OK = True
except Exception as e:
    LOGFIRE_STATUS = f"Standby ({e})"
    LOGFIRE_OK = False

# --- HTTP CONNECTION POOLING (PERFORMANCE BOOST) ---
@st.cache_resource
def get_http_session() -> requests.Session:
    """Reuses TCP/HTTP connections to the backend rather than handshaking every request."""
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=1)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def check_backend_health() -> tuple[bool, str]:
    """Lightweight health probe to verify FastAPI is reachable."""
    try:
        session = get_http_session()
        resp = session.get(f"{BACKEND_URL}/", timeout=1.5)
        if resp.status_code == 200:
            return True, "Online (200 OK)"
        return False, f"Degraded (HTTP {resp.status_code})"
    except Exception:
        return False, "Offline"


# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Enterprise Agentic RAG",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- MODERN STYLING (CSS) ---
st.markdown(
    """
    <style>
    /* Metric pills */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-green { background-color: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-red { background-color: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-blue { background-color: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.3); }
    .badge-purple { background-color: rgba(168, 85, 247, 0.15); color: #a855f7; border: 1px solid rgba(168, 85, 247, 0.3); }

    /* Source Cards */
    .source-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 3px solid #3b82f6;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 0.9rem;
    }

    /* Step Pill */
    .step-pill {
        font-family: monospace;
        font-size: 0.82rem;
        padding: 2px 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
        margin-bottom: 4px;
        display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- AVATARS ---
AI_AVATAR = "🤖"
USER_AVATAR = "👤"

# --- SESSION STATE ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    logfire.info(f"✨ New User Session Created: {st.session_state.session_id}")

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- FAST STREAMING GENERATOR ---
def stream_word_chunks(text: str):
    """
    High-performance word streamer: streams words with micro-delay (12ms).
    Renders 10x faster than character-by-character loops while maintaining natural fluidity.
    """
    words = text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        time.sleep(0.012)


# --- SIDEBAR CONTROLS ---
backend_ok, backend_msg = check_backend_health()

with st.sidebar:
    st.title("🧠 Agent OS")
    st.caption("Enterprise RAG Orchestration")
    st.markdown("---")

    # Backend Status
    st.markdown("### 🔌 System Services")
    if backend_ok:
        st.markdown(f'<span class="status-badge badge-green">● Backend: {backend_msg}</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="status-badge badge-red">● Backend: {backend_msg}</span>', unsafe_allow_html=True)
        st.warning(
            "Backend is offline. Start it in terminal:\n\n"
            "`uvicorn app.main:app --port 8000`"
        )

    # Logfire Status
    if LOGFIRE_OK:
        st.markdown(f'<span class="status-badge badge-blue">● Logfire: Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="status-badge badge-purple">● Logfire: {LOGFIRE_STATUS}</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"**Session Thread:** `{st.session_state.session_id[:8]}...`")
    st.markdown(f"**Messages in Context:** `{len(st.session_state.messages)}`")

    # Quick Prompt Starters
    st.markdown("---")
    st.markdown("### 💡 Quick Starters")
    starter_prompts = [
        "How do I configure Intel SRIOV on Kubernetes?",
        "Explain Pod autoscaling in Kubernetes",
        "Tell me a joke",
        "What can you do?",
    ]

    for p in starter_prompts:
        if st.button(p, key=f"btn_{p}", use_container_width=True):
            st.session_state["pending_prompt"] = p
            st.rerun()

    # Architecture Graph Preview
    st.markdown("---")
    with st.expander("🗺️ Workflow Architecture"):
        if backend_ok:
            st.image(f"{BACKEND_URL}/graph", caption="LangGraph Mermaid Workflow", use_container_width=True)
        else:
            st.info("Start backend to view live workflow graph.")

    # Reset Conversation
    st.markdown("---")
    if st.button("🗑️ Clear History & Memory", use_container_width=True, type="primary"):
        logfire.warning(f"🗑️ Memory Wipe Triggered for session: {st.session_state.session_id}")
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()


# --- MAIN HEADER ---
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.title("🤖 Enterprise Agentic Assistant")
    st.caption("Grounded Knowledge Retrieval • FlashRank Cross-Encoder • NeMo Guardrails")
with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()


# --- DISPLAY CONVERSATION HISTORY ---
for msg in st.session_state.messages:
    role = msg["role"]
    avatar = AI_AVATAR if role == "assistant" else USER_AVATAR
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])

        # Retain thought process and sources in past history for full inspection
        thought_steps = msg.get("thought_process", [])
        sources = msg.get("sources", [])
        latency = msg.get("latency")

        if thought_steps or sources or latency:
            with st.expander("🔍 Inspection & Verification", expanded=False):
                if latency:
                    st.caption(f"⚡ Synthesis time: **{latency:.2f}s**")
                if thought_steps:
                    st.markdown("**Reasoning Steps:**")
                    for step in thought_steps:
                        st.markdown(f'<div class="step-pill">⚙️ {step}</div>', unsafe_allow_html=True)
                if sources:
                    st.markdown(f"**Retrieved Sources ({len(sources)} chunks):**")
                    for i, source in enumerate(sources):
                        st.markdown(f'<div class="source-box"><strong>Chunk {i+1}:</strong><br>{source}</div>', unsafe_allow_html=True)


# --- CHAT INPUT HANDLING ---
# Unconditionally render chat_input so the input bar is ALWAYS anchored at the bottom
chat_input_val = st.chat_input("Ask a technical question or conversation...")

user_query = None
if chat_input_val:
    user_query = chat_input_val
elif st.session_state.get("pending_prompt"):
    user_query = st.session_state.pop("pending_prompt")

if user_query:
    # 1. Append & Display User Message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(user_query)

    # 2. Assistant Response Container
    with st.chat_message("assistant", avatar=AI_AVATAR):
        t_start = time.time()
        data = {}

        with st.status("🔍 Agent is reasoning...", expanded=True) as status_box:
            try:
                session = get_http_session()
                url = f"{BACKEND_URL}/query"
                payload = {"q": user_query, "thread_id": st.session_state.session_id}

                # HTTP Call with trace span
                with logfire.span("📡 Calling RAG Backend", user_query=user_query):
                    resp = session.post(url, json=payload, timeout=60)

                if resp.status_code != 200:
                    status_box.update(label="❌ Backend Error", state="error", expanded=True)
                    st.error(f"Backend responded with HTTP {resp.status_code}: {resp.text}")
                    st.stop()

                data = resp.json()
                t_elapsed = time.time() - t_start

                # Display Thought Steps
                steps = data.get("thought_process", [])
                for step in steps:
                    st.write(f"⚙️ {step}")

                # Update Status Box
                status_box.update(
                    label=f"✅ Response Ready ({t_elapsed:.2f}s)",
                    state="complete",
                    expanded=False,
                )

            except requests.exceptions.ConnectionError:
                status_box.update(label="❌ Connection Failed", state="error", expanded=True)
                st.error(
                    f"Could not connect to FastAPI backend at `{BACKEND_URL}`.\n\n"
                    "Make sure the backend is running:\n"
                    "```powershell\n"
                    "uvicorn app.main:app --port 8000\n"
                    "```"
                )
                st.stop()
            except Exception as e:
                logfire.error(f"❌ UI-Backend Connection Failed: {e}")
                status_box.update(label="❌ Processing Error", state="error", expanded=True)
                st.error(f"Unexpected error: {e}")
                st.stop()

        # 3. Stream Final Answer Fluidly
        full_answer = data.get("answer", "No response received.")
        answer_text = st.write_stream(stream_word_chunks(full_answer))

        # 4. Show Context Sources in Clean Cards
        sources = data.get("sources", [])
        if sources:
            with st.expander(f"📄 Retrieved Sources ({len(sources)} grounded chunks)", expanded=False):
                for i, source in enumerate(sources):
                    preview_title = source[:80].replace("\n", " ").replace("CONTENT:", "").strip() + "..."
                    with st.expander(f"Source {i+1} — {preview_title}"):
                        st.info(source)

        # 5. Store in Session History with Full Audit Info
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_answer,
            "thought_process": steps,
            "sources": sources,
            "latency": t_elapsed,
        })
