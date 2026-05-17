import streamlit as st

import client_api

st.set_page_config(
    page_title="MedicalGPT",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #0f1117; }
    .block-container { padding-top: 2rem; }
    .scholar-header { text-align: center; padding: 1.5rem 0 1rem; }
    .scholar-header h1 {
        font-size: 2.4rem; font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .scholar-header p { color: #9ca3af; font-size: 1rem; margin-top: 0.3rem; }
    .source-card {
        background: #1e2130; border-left: 3px solid #6366f1; border-radius: 6px;
        padding: 0.6rem 0.8rem; margin: 0.4rem 0; font-size: 0.82rem; color: #d1d5db;
    }
    .source-score { color: #6366f1; font-weight: 600; }
    .collection-badge {
        background: #312e81; color: #a5b4fc; padding: 0.2rem 0.6rem;
        border-radius: 12px; font-size: 0.78rem; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def init_session():
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("active_collection", None)
    st.session_state.setdefault("collections", [])
    st.session_state.setdefault("sources_for_last_msg", [])


def refresh_collections():
    try:
        r = client_api.list_collections()
        st.session_state.collections = r.json().get("collections", []) if r.ok else []
    except Exception:
        st.session_state.collections = []


def sidebar():
    with st.sidebar:
        st.markdown("## 📚 MedicalGPT")
        st.markdown("---")

        st.markdown("### New Collection")
        new_col = st.text_input("Collection name", placeholder="e.g. cardiology-notes", key="new_col_input")
        uploaded = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True, key="pdf_uploader")

        if st.button("Create & Index", type="primary", use_container_width=True):
            if not new_col.strip():
                st.error("Enter a collection name.")
            elif not uploaded:
                st.error("Upload at least one PDF.")
            else:
                with st.spinner(f"Indexing {len(uploaded)} PDF(s)…"):
                    try:
                        r = client_api.upload_pdfs(uploaded, new_col.strip())
                        if r.ok:
                            data = r.json()
                            st.success(f"Indexed {data['chunks_indexed']} chunks into **{data['collection']}**")
                            st.session_state.active_collection = data["collection"]
                            st.session_state.chat_history = []
                            st.session_state.sources_for_last_msg = []
                            refresh_collections()
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {r.text}")
                    except Exception as e:
                        st.error(f"Backend error: {e}")

        st.markdown("---")
        st.markdown("### Your Collections")
        refresh_collections()
        if not st.session_state.collections:
            st.caption("No collections yet. Upload PDFs above.")
        else:
            for col in st.session_state.collections:
                c1, c2 = st.columns([3, 1])
                is_active = col == st.session_state.active_collection
                if c1.button(f"{'✅ ' if is_active else ''}{col}", key=f"sel_{col}", use_container_width=True):
                    st.session_state.active_collection = col
                    st.session_state.chat_history = []
                    st.session_state.sources_for_last_msg = []
                    st.rerun()
                if c2.button("🗑", key=f"del_{col}", help="Delete collection"):
                    with st.spinner("Deleting…"):
                        client_api.delete_collection(col)
                    if st.session_state.active_collection == col:
                        st.session_state.active_collection = None
                        st.session_state.chat_history = []
                    refresh_collections()
                    st.rerun()

        st.markdown("---")
        st.caption("FastAPI · Groq · Pinecone · LangChain")


def main_area():
    st.markdown("""
    <div class="scholar-header">
        <h1>MedicalGPT</h1>
        <p>Upload documents — ask anything, get cited answers.</p>
    </div>
    """, unsafe_allow_html=True)

    active = st.session_state.active_collection
    if not active:
        st.info("👈 Create a collection by uploading PDFs in the sidebar to get started.")
        return

    c1, c2 = st.columns([6, 1])
    with c1:
        st.markdown(f'Active collection: <span class="collection-badge">📁 {active}</span>', unsafe_allow_html=True)
    with c2:
        if st.button("Summarize", use_container_width=True):
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Summarizing…"):
                    try:
                        r = client_api.summarize(active)
                        summary = r.json().get("answer", "") if r.ok else f"Error: {r.text}"
                    except Exception as e:
                        summary = f"Backend error: {e}"
                st.markdown(summary)
            st.session_state.chat_history.append({"role": "assistant", "content": summary})

    st.markdown("---")

    for msg in st.session_state.chat_history:
        avatar = "🧑" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask anything about your documents…"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.chat_history[:-1]
        ]

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking…"):
                try:
                    r = client_api.ask_question(prompt, active, history)
                    if r.ok:
                        data = r.json()
                        answer = data.get("answer", "")
                        sources = data.get("sources", [])
                    else:
                        answer, sources = f"Error: {r.text}", []
                except Exception as e:
                    answer, sources = f"Backend error: {e}", []
            st.markdown(answer)

        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.session_state.sources_for_last_msg = sources

        if sources:
            with st.expander(f"📎 Sources ({len(sources)} chunks retrieved)", expanded=False):
                for i, s in enumerate(sources, 1):
                    st.markdown(
                        f'<div class="source-card">'
                        f'<b>Source {i}</b> · {s["source"]} · Page {s["page"]} · '
                        f'<span class="source-score">Relevance: {s["score"]}</span>'
                        f'<br><small>{s["snippet"]}…</small></div>',
                        unsafe_allow_html=True,
                    )


def main():
    init_session()
    sidebar()
    main_area()


if __name__ == "__main__":
    main()
