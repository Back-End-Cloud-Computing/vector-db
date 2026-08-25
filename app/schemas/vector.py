from typing import Any

from pydantic import BaseModel, Field


class VectorItem(BaseModel):
    product_id: str = Field(..., min_length=1)
    embedding: list[float] = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    document: str = Field(..., min_length=1)


class InsertRequest(BaseModel):
    items: list[VectorItem] = Field(..., min_length=1)


class InsertResponse(BaseModel):
    upserted: int
    ids: list[str]


class SearchRequest(BaseModel):
    embedding: list[float] = Field(..., min_length=1)
    n_results: int = Field(default=10, ge=1, le=100)
    where: dict[str, Any] | None = None


class SearchResponse(BaseModel):
    ids: list[str]
    distances: list[float]
    metadatas: list[dict[str, Any]]
    documents: list[str]


class DeleteRequest(BaseModel):
    ids: list[str] | None = None
    where: dict[str, Any] | None = None


class DeleteResponse(BaseModel):
    deleted: bool


class CollectionsResponse(BaseModel):
    collections: list[str]
