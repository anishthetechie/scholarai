from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from rag.chain import answer_question, summarize_collection

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    question: str
    collection: str
    history: Optional[List[ChatMessage]] = []


class SummarizeRequest(BaseModel):
    collection: str


@router.post("/ask/")
async def ask(req: AskRequest):
    try:
        history = [{"role": m.role, "content": m.content} for m in (req.history or [])]
        answer, sources = answer_question(req.question, req.collection, history)
        return {"answer": answer, "sources": sources}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/summarize/")
async def summarize(req: SummarizeRequest):
    try:
        summary, _ = summarize_collection(req.collection)
        return {"answer": summary, "sources": []}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
