from fastapi import APIRouter

from app.database import chromadb_client
from app.schemas.vector import (
    CollectionsResponse,
    DeleteRequest,
    DeleteResponse,
    InsertRequest,
    InsertResponse,
    SearchRequest,
    SearchResponse,
)
from app.services import vector_service

router = APIRouter(prefix="/vector_db", tags=["vector_db"])


@router.get("/collections", response_model=CollectionsResponse)
async def list_collections() -> CollectionsResponse:
    collections = await chromadb_client.list_collections()
    return CollectionsResponse(collections=collections)


@router.post("/insert", response_model=InsertResponse)
async def insert(payload: InsertRequest) -> InsertResponse:
    upserted, ids = await vector_service.insert_batch(payload)
    return InsertResponse(upserted=upserted, ids=ids)


@router.post("/search", response_model=SearchResponse)
async def search(payload: SearchRequest) -> SearchResponse:
    return await vector_service.search(payload)


@router.post("/delete", response_model=DeleteResponse)
async def delete(payload: DeleteRequest) -> DeleteResponse:
    deleted = await vector_service.delete(payload)
    return DeleteResponse(deleted=deleted)
