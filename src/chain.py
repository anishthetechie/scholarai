import os
from typing import Generator, List, Tuple

from groq import Groq

from .retriever import retrieve_context

SYSTEM_PROMPT = """You are ScholarAI, an intelligent research assistant. Your job is to help users understand documents, research papers, and reports by answering their questions accurately and concisely.

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
        page = meta["page"] + 1
        parts.append(f"[Source {i}: {source}, Page {page}]\n{text}")
    return "\n\n---\n\n".join(parts)


def stream_answer(
    query: str,
    namespace: str,
    chat_history: List[dict],
) -> Tuple[Generator, List[Tuple[str, dict]]]:
    chunks = retrieve_context(query, namespace)

    if not chunks:
        def empty_gen():
            yield "I couldn't find relevant information in the uploaded documents to answer your question. Please make sure you've uploaded the relevant documents to this collection."
        return empty_gen(), []

    context_str = build_context_str(chunks)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in chat_history[-6:]:
        messages.append(msg)
    messages.append({
        "role": "user",
        "content": f"Context from documents:\n\n{context_str}\n\nQuestion: {query}",
    })

    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    stream = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.2,
        max_tokens=1024,
        stream=True,
    )

    def token_gen():
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    return token_gen(), chunks


def summarize_collection(namespace: str) -> Generator:
    from .retriever import retrieve_context as rc

    sample_chunks = rc("summarize all main topics and findings", namespace, top_k=10)
    if not sample_chunks:
        def err():
            yield "No documents found in this collection to summarize."
        return err()

    context_str = build_context_str(sample_chunks)

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    stream = client.chat.completions.create(
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
        stream=True,
    )

    def token_gen():
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    return token_gen()
