from typing import Any

from pydantic import BaseModel, Field


class VectorItem(BaseModel):
    id: str = Field(..., min_length=1)
    embedding: list[float] = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    document: str = Field(..., min_length=1)


class InsertRequest(BaseModel):
    collection_name: str = Field(..., min_length=1, description="Chroma collection this batch is inserted into.")
    items: list[VectorItem] = Field(..., min_length=1)


class InsertResponse(BaseModel):
    upserted: int
    ids: list[str]


class SearchRequest(BaseModel):
    collection_name: str = Field(..., min_length=1, description="Chroma collection to search in.")
    embedding: list[float] = Field(..., min_length=1)
    n_results: int = Field(default=10, ge=1, le=100)
    where: dict[str, Any] | None = None


class SearchResponse(BaseModel):
    ids: list[str]
    distances: list[float]
    metadatas: list[dict[str, Any]]
    documents: list[str]


class DeleteRequest(BaseModel):
    collection_name: str = Field(..., min_length=1, description="Chroma collection to delete from.")
    ids: list[str] | None = None
    where: dict[str, Any] | None = None


class DeleteResponse(BaseModel):
    deleted: bool


class CollectionsResponse(BaseModel):
    collections: list[str]


class CountResponse(BaseModel):
    collection_name: str
    count: int
