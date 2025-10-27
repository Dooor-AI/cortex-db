"""
Backend de exemplo usando FastAPI + CortexDB SDK.

Como rodar:
    pip install fastapi uvicorn
    python playground/backend_example.py

Endpoints:
    POST /products - Criar produto
    GET /products/{id} - Buscar produto
    GET /products/search?q=query - Buscar produtos por texto
    DELETE /products/{id} - Deletar produto
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from cortexdb import CortexClient, FieldDefinition, FieldType


# Models
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int


class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    stock: int


# Global client
cortex: Optional[CortexClient] = None
COLLECTION = "products"


# Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    global cortex

    # Startup
    print("Starting CortexDB client...")
    cortex = CortexClient("http://localhost:8000")
    await cortex.__aenter__()

    # Criar collection se não existir
    try:
        await cortex.collections.get(COLLECTION)
        print(f"Collection '{COLLECTION}' já existe")
    except:
        print(f"Criando collection '{COLLECTION}'...")
        await cortex.collections.create(
            name=COLLECTION,
            fields=[
                FieldDefinition(name="name", type=FieldType.STRING),
                FieldDefinition(name="description", type=FieldType.TEXT, vectorize=True),
                FieldDefinition(name="price", type=FieldType.FLOAT),
                FieldDefinition(name="stock", type=FieldType.INT),
            ],
        )

    yield

    # Shutdown
    print("Closing CortexDB client...")
    await cortex.__aexit__(None, None, None)


app = FastAPI(title="Products API - CortexDB Example", lifespan=lifespan)


# Endpoints
@app.post("/products", response_model=Product)
async def create_product(product: ProductCreate):
    """Criar novo produto."""
    record = await cortex.records.create(
        collection=COLLECTION,
        data=product.model_dump(),
    )

    return Product(id=record.id, **product.model_dump())


@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Buscar produto por ID."""
    try:
        record = await cortex.records.get(COLLECTION, product_id)
        return Product(id=record.id, **record.data)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Product not found")


@app.get("/products/search/")
async def search_products(q: str, limit: int = 10):
    """Buscar produtos por texto (semantic search)."""
    results = await cortex.records.query(
        collection=COLLECTION,
        query=q,
        limit=limit,
    )

    return [
        {"id": r.id, "score": r.score, "product": Product(id=r.id, **r.data)}
        for r in results
    ]


@app.delete("/products/{product_id}")
async def delete_product(product_id: str):
    """Deletar produto."""
    try:
        await cortex.records.delete(COLLECTION, product_id)
        return {"status": "deleted", "id": product_id}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Product not found")


@app.get("/health")
async def health():
    """Health check."""
    cortex_healthy = await cortex.healthcheck()
    return {"status": "ok", "cortex": "connected" if cortex_healthy else "disconnected"}


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("  Products API - CortexDB Example")
    print("=" * 60)
    print("\nEndpoints disponíveis:")
    print("  - POST   http://localhost:8001/products")
    print("  - GET    http://localhost:8001/products/{id}")
    print("  - GET    http://localhost:8001/products/search?q=query")
    print("  - DELETE http://localhost:8001/products/{id}")
    print("  - GET    http://localhost:8001/health")
    print("\nDocs: http://localhost:8001/docs")
    print("=" * 60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8001)
