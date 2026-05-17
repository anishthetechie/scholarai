import os
from typing import List, Tuple

from groq import Groq

from .retriever import retrieve_context

SYSTEM_PROMPT = """You are MedicalGPT, an intelligent research assistant. Your job is to help users understand documents, research papers, and reports by answering their questions accurately and concisely.

Guidelines:
- Answer ONLY based on the provided context. Do not hallucinate or use outside knowledge.
- If the context doesn't contain enough information to answer, say so clearly.
- Cite the document source and page number when referencing specific information.
- Be concise but thorough. Use bullet points for lists and structured information.
- If asked to summarize, provide a structured summary with key points.
"""


def build_context_str(chunks: List[Tuple[str, dict]]) -> str:
    parts = []
    for i, (text, meta) in enumerate(chunks, 1):
        source = os.path.basename(meta["source"])
        page = int(meta["page"]) + 1
        parts.append(f"[Source {i}: {source}, Page {page}]\n{text}")
    return "\n\n---\n\n".join(parts)


def answer_question(
    query: str,
    namespace: str,
    chat_history: List[dict],
) -> Tuple[str, List[dict]]:
    chunks = retrieve_context(query, namespace)

    if not chunks:
        return (
            "I couldn't find relevant information in the uploaded documents to "
            "answer your question. Please make sure you've uploaded the relevant "
            "documents to this collection.",
            [],
        )

    context_str = build_context_str(chunks)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in chat_history[-6:]:
        messages.append(msg)
    messages.append({
        "role": "user",
        "content": f"Context from documents:\n\n{context_str}\n\nQuestion: {query}",
    })

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.2,
        max_tokens=1024,
    )
    answer = resp.choices[0].message.content

    sources = [
        {
            "source": os.path.basename(meta["source"]) or "Document",
            "page": int(meta["page"]) + 1,
            "score": meta["score"],
            "snippet": text[:250],
        }
        for text, meta in chunks
    ]
    return answer, sources


def summarize_collection(namespace: str) -> Tuple[str, List[dict]]:
    chunks = retrieve_context("summarize all main topics and findings", namespace, top_k=10)
    if not chunks:
        return "No documents found in this collection to summarize.", []

    context_str = build_context_str(chunks)

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Based on the following document excerpts, provide a comprehensive structured summary with:\n1. Main topics covered\n2. Key findings or arguments\n3. Important conclusions\n\nDocument excerpts:\n{context_str}",
            },
        ],
        temperature=0.3,
        max_tokens=1500,
    )
    return resp.choices[0].message.content, []
