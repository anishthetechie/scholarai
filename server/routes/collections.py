from fastapi import APIRouter
from fastapi.responses import JSONResponse

from rag.processor import delete_namespace, list_namespaces

router = APIRouter()


@router.get("/collections/")
async def get_collections():
    try:
        return {"collections": list_namespaces()}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.delete("/collections/{name}")
async def remove_collection(name: str):
    try:
        delete_namespace(name)
        return {"deleted": name}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
