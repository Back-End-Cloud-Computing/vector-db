class VectorDbError(Exception):
    """Base exception for the vector-db domain."""


class VectorStoreError(VectorDbError):
    """Raised when a ChromaDB operation fails."""


class ProductVectorNotFoundError(VectorDbError):
    """Raised when a product's vector is not indexed yet (e.g. similarity lookup)."""

    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Product '{product_id}' has no indexed vector")
