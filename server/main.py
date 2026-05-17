import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from routes.ask import router as ask_router
from routes.collections import router as collections_router
from routes.upload import router as upload_router

app = FastAPI(
    title="MedicalGPT API",
    description="RAG backend for the MedicalGPT document intelligence assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedicalGPT API"}


app.include_router(upload_router)
app.include_router(ask_router)
app.include_router(collections_router)
