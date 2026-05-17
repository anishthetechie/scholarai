import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

for _key in ("GROQ_API_KEY", "PINECONE_API_KEY", "GOOGLE_API_KEY"):
    if not os.environ.get(_key):
        try:
            os.environ[_key] = st.secrets[_key]
        except Exception:
            pass

from src.chain import stream_answer, summarize_collection
from src.processor import delete_namespace, list_namespaces, process_and_index_pdfs

st.set_page_config(
    page_title="ScholarAI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0f1117; }
    .main { background-color: #0f1117; }
    .block-container { padding-top: 2rem; }

    .scholar-header {
        text-align: center;
        padding: 1.5rem 0 1rem;
    }
    .scholar-header h1 {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .scholar-header p {
        color: #9ca3af;
        font-size: 1rem;
        margin-top: 0.3rem;
    }

    .source-card {
        background: #1e2130;
        border-left: 3px solid #6366f1;
        border-radius: 6px;
        padding: 0.6rem 0.8rem;
        margin: 0.4rem 0;
        font-size: 0.82rem;
        color: #d1d5db;
    }
    .source-score {
        color: #6366f1;
        font-weight: 600;
    }

    .collection-badge {
        background: #312e81;
        color: #a5b4fc;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
    }

    .stChatMessage { border-radius: 12px; }
    div[data-testid="stChatMessageContent"] p { font-size: 0.95rem; line-height: 1.6; }

    .upload-section {
        background: #1a1d2e;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "active_collection" not in st.session_state:
        st.session_state.active_collection = None
    if "collections" not in st.session_state:
        st.session_state.collections = []
    if "sources_for_last_msg" not in st.session_state:
        st.session_state.sources_for_last_msg = []


def refresh_collections():
    try:
        st.session_state.collections = list_namespaces()
    except Exception:
        st.session_state.collections = []


def sidebar():
    with st.sidebar:
        st.markdown("## 📚 ScholarAI")
        st.markdown("---")

        st.markdown("### New Collection")
        new_col_name = st.text_input("Collection name", placeholder="e.g. quantum-physics", key="new_col_input")
        uploaded_files = st.file_uploader(
            "Upload PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            key="pdf_uploader",
        )

        if st.button("Create & Index", type="primary", use_container_width=True):
            if not new_col_name.strip():
                st.error("Enter a collection name.")
            elif not uploaded_files:
                st.error("Upload at least one PDF.")
            else:
                collection = new_col_name.strip().lower().replace(" ", "-")
                with st.spinner(f"Indexing {len(uploaded_files)} PDF(s)..."):
                    tmp_paths = []
                    for f in uploaded_files:
                        suffix = os.path.splitext(f.name)[1]
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                            tmp.write(f.read())
                            tmp_paths.append(tmp.name)
                    try:
                        count = process_and_index_pdfs(tmp_paths, namespace=collection)
                        st.success(f"Indexed {count} chunks into **{collection}**")
                        refresh_collections()
                        st.session_state.active_collection = collection
                        st.session_state.chat_history = []
                        st.session_state.sources_for_last_msg = []
                        st.rerun()
                    except Exception as e:
                        st.error(f"Indexing failed: {e}")
                    finally:
                        for p in tmp_paths:
                            try:
                                os.unlink(p)
                            except Exception:
                                pass

        st.markdown("---")
        st.markdown("### Your Collections")

        refresh_collections()
        if not st.session_state.collections:
            st.caption("No collections yet. Upload PDFs above.")
        else:
            for col in st.session_state.collections:
                cols = st.columns([3, 1])
                is_active = col == st.session_state.active_collection
                label = f"{'✅ ' if is_active else ''}{col}"
                if cols[0].button(label, key=f"sel_{col}", use_container_width=True):
                    st.session_state.active_collection = col
                    st.session_state.chat_history = []
                    st.session_state.sources_for_last_msg = []
                    st.rerun()
                if cols[1].button("🗑", key=f"del_{col}", help="Delete collection"):
                    with st.spinner("Deleting..."):
                        delete_namespace(col)
                    if st.session_state.active_collection == col:
                        st.session_state.active_collection = None
                        st.session_state.chat_history = []
                    refresh_collections()
                    st.rerun()

        st.markdown("---")
        st.caption("Powered by Groq · Pinecone · LangChain")


def main_area():
    st.markdown("""
    <div class="scholar-header">
        <h1>ScholarAI</h1>
        <p>Upload research papers & documents — ask anything, get cited answers.</p>
    </div>
    """, unsafe_allow_html=True)

    active = st.session_state.active_collection

    if not active:
        st.info("👈 Create a collection by uploading PDFs in the sidebar to get started.")
        return

    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown(f'Active collection: <span class="collection-badge">📁 {active}</span>', unsafe_allow_html=True)
    with col2:
        if st.button("Summarize", use_container_width=True):
            with st.chat_message("assistant", avatar="🤖"):
                placeholder = st.empty()
                full = ""
                for token in summarize_collection(active):
                    full += token
                    placeholder.markdown(full + "▌")
                placeholder.markdown(full)
            st.session_state.chat_history.append({"role": "assistant", "content": full})

    st.markdown("---")

    for i, msg in enumerate(st.session_state.chat_history):
        avatar = "🧑" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask anything about your documents…"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        history_for_llm = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.chat_history[:-1]
        ]

        with st.chat_message("assistant", avatar="🤖"):
            placeholder = st.empty()
            full_response = ""
            try:
                token_gen, sources = stream_answer(prompt, active, history_for_llm)
                for token in token_gen:
                    full_response += token
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                st.session_state.sources_for_last_msg = sources
            except Exception as e:
                full_response = f"An error occurred: {e}"
                placeholder.markdown(full_response)
                sources = []

        st.session_state.chat_history.append({"role": "assistant", "content": full_response})

        if st.session_state.sources_for_last_msg:
            with st.expander(f"📎 Sources ({len(st.session_state.sources_for_last_msg)} chunks retrieved)", expanded=False):
                for i, (text, meta) in enumerate(st.session_state.sources_for_last_msg, 1):
                    source_name = os.path.basename(meta["source"]) or "Document"
                    page = int(meta["page"]) + 1
                    score = meta["score"]
                    st.markdown(
                        f'<div class="source-card">'
                        f'<b>Source {i}</b> · {source_name} · Page {page} · '
                        f'<span class="source-score">Relevance: {score}</span>'
                        f'<br><small>{text[:250]}…</small>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )


def main():
    init_session()
    sidebar()
    main_area()


if __name__ == "__main__":
    main()
