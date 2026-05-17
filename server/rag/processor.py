import os
import time
import uuid
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone, ServerlessSpec


PINECONE_INDEX_NAME = "scholarai"
EMBEDDING_DIMENSION = 3072


def get_pinecone_index():
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    existing = [idx.name for idx in pc.list_indexes()]
    if PINECONE_INDEX_NAME not in existing:
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
            time.sleep(1)
    return pc.Index(PINECONE_INDEX_NAME)


def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )


def process_and_index_pdfs(pdf_paths: List[str], namespace: str) -> int:
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    all_docs = []

    for path in pdf_paths:
        loader = PyPDFLoader(path)
        pages = loader.load()
        chunks = splitter.split_documents(pages)
        all_docs.extend(chunks)

    if not all_docs:
        return 0

    embeddings_model = get_embeddings()
    index = get_pinecone_index()

    texts = [doc.page_content for doc in all_docs]
    metadatas = [
        {
            "text": doc.page_content,
            "source": doc.metadata.get("source", ""),
            "page": doc.metadata.get("page", 0),
        }
        for doc in all_docs
    ]

    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_meta = metadatas[i : i + batch_size]
        vectors = embeddings_model.embed_documents(batch_texts)
        upsert_data = [
            (str(uuid.uuid4()), vec, meta)
            for vec, meta in zip(vectors, batch_meta)
        ]
        index.upsert(vectors=upsert_data, namespace=namespace)

    return len(all_docs)


def list_namespaces() -> List[str]:
    index = get_pinecone_index()
    stats = index.describe_index_stats()
    return list(stats.namespaces.keys())


def delete_namespace(namespace: str) -> None:
    index = get_pinecone_index()
    index.delete(delete_all=True, namespace=namespace)
