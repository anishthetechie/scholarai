import os
from typing import List, Tuple

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from .processor import get_pinecone_index


def retrieve_context(query: str, namespace: str, top_k: int = 5) -> List[Tuple[str, dict]]:
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )
    query_vector = embeddings_model.embed_query(query)
    index = get_pinecone_index()

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True,
    )

    chunks = []
    for match in results.matches:
        if match.metadata:
            text = match.metadata.get("text", "")
            meta = {
                "source": match.metadata.get("source", "Unknown"),
                "page": match.metadata.get("page", 0),
                "score": round(match.score, 3),
            }
            chunks.append((text, meta))

    return chunks
