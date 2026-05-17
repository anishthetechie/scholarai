import requests

from config import API_URL

TIMEOUT = 120


def upload_pdfs(files, collection: str):
    payload = [("files", (f.name, f.getvalue(), "application/pdf")) for f in files]
    return requests.post(
        f"{API_URL}/upload_pdfs/",
        files=payload,
        data={"collection": collection},
        timeout=TIMEOUT,
    )


def list_collections():
    return requests.get(f"{API_URL}/collections/", timeout=30)


def delete_collection(name: str):
    return requests.delete(f"{API_URL}/collections/{name}", timeout=60)


def ask_question(question: str, collection: str, history: list):
    return requests.post(
        f"{API_URL}/ask/",
        json={"question": question, "collection": collection, "history": history},
        timeout=TIMEOUT,
    )


def summarize(collection: str):
    return requests.post(
        f"{API_URL}/summarize/",
        json={"collection": collection},
        timeout=TIMEOUT,
    )
