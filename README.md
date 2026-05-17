# ScholarAI 📚

An AI-powered research assistant that lets you upload PDFs and ask intelligent questions — with cited answers pulled directly from your documents.

Built with RAG (Retrieval-Augmented Generation) using **Groq**, **Pinecone**, and **Google Embeddings**.

## Features

- **Upload any PDF** — research papers, textbooks, reports, manuals
- **Named Collections** — organise documents into separate topic groups
- **Cited Answers** — every response shows which document and page it came from
- **Document Summaries** — one-click structured summary of any collection
- **Streaming Responses** — real-time token-by-token output via Groq
- **Multi-turn Conversations** — maintains chat history for follow-up questions

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| LLM | Groq (llama-3.3-70b-versatile) |
| Embeddings | Google Generative AI (gemini-embedding-001) |
| Vector DB | Pinecone (Serverless) |
| RAG | LangChain |

## Local Setup

```bash
git clone https://github.com/anishthetechie/scholarai.git
cd scholarai
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
streamlit run app.py
```

## Required API Keys

| Variable | Where to get it |
|----------|----------------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) |
| `PINECONE_API_KEY` | [app.pinecone.io](https://app.pinecone.io) |
| `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com) |

## How It Works

1. **Upload** — PDFs are split into 800-character chunks with 100-char overlap
2. **Embed** — Each chunk is embedded using Google's `gemini-embedding-001` (3072 dims)
3. **Index** — Vectors are stored in Pinecone under your collection's namespace
4. **Query** — Your question is embedded and matched against stored vectors (top-5)
5. **Answer** — Groq's LLM reads the retrieved context and generates a cited answer
