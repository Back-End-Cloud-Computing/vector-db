from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import ProductVectorNotFoundError, VectorStoreError
from app.core.logging import configure_logging
from app.database import chromadb_client
from app.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    chromadb_client.connect_to_chromadb()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description=(
            "Microsservico de banco vetorial: persistencia de embeddings no ChromaDB, "
            "busca KNN/semantica e recomendacao. Nunca gera embeddings - recebe vetores "
            "prontos do embedding-reranking."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    application.include_router(api_router)

    @application.exception_handler(VectorStoreError)
    async def vector_store_error_handler(request: Request, exc: VectorStoreError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc), "error_type": "vector_store_error"})

    @application.exception_handler(ProductVectorNotFoundError)
    async def product_vector_not_found_handler(
        request: Request, exc: ProductVectorNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc), "error_type": "product_vector_not_found"})

    @application.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
