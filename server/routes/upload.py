import os
import tempfile
from typing import List

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from rag.processor import process_and_index_pdfs

router = APIRouter()


@router.post("/upload_pdfs/")
async def upload_pdfs(
    files: List[UploadFile] = File(...),
    collection: str = Form(...),
):
    tmp_paths = []
    try:
        namespace = collection.strip().lower().replace(" ", "-")
        if not namespace:
            return JSONResponse(status_code=400, content={"error": "Collection name required"})

        for f in files:
            suffix = os.path.splitext(f.filename)[1] or ".pdf"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await f.read())
                tmp_paths.append(tmp.name)

        count = process_and_index_pdfs(tmp_paths, namespace=namespace)
        return {"collection": namespace, "chunks_indexed": count}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        for p in tmp_paths:
            try:
                os.unlink(p)
            except OSError:
                pass
