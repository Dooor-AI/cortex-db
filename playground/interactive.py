"""
Script para rodar em modo interativo.

Como usar:
    python3 -i playground/interactive.py

Depois você pode usar diretamente no terminal:
    >>> records = await create_sample_data()
    >>> results = await search("python programming")
    >>> await cleanup()
"""

import asyncio

from cortexdb import CortexClient, FieldDefinition, FieldType

# Global client
client = None
COLLECTION = "interactive_test"


async def init():
    """Inicializar client."""
    global client
    if client is None:
        client = CortexClient("http://localhost:8000")
        await client.__aenter__()
        print("✓ Client conectado")
    return client


async def create_collection():
    """Criar collection de teste."""
    await init()

    try:
        await client.collections.delete(COLLECTION)
        print(f"(deletou collection antiga)")
    except:
        pass

    schema = await client.collections.create(
        name=COLLECTION,
        fields=[
            FieldDefinition(name="title", type=FieldType.STRING),
            FieldDefinition(name="content", type=FieldType.TEXT, vectorize=True),
            FieldDefinition(name="category", type=FieldType.STRING),
        ],
    )
    print(f"✓ Collection '{COLLECTION}' criada")
    return schema


async def create_sample_data():
    """Criar dados de exemplo."""
    await init()

    docs = [
        {
            "title": "Python Basics",
            "content": "Learn Python programming from scratch",
            "category": "programming",
        },
        {
            "title": "Machine Learning",
            "content": "Introduction to ML algorithms",
            "category": "ai",
        },
        {
            "title": "Web Development",
            "content": "Build websites with HTML and JavaScript",
            "category": "web",
        },
    ]

    records = []
    for doc in docs:
        record = await client.records.create(collection=COLLECTION, data=doc)
        records.append(record)
        print(f"✓ Created: {doc['title']}")

    return records


async def search(query: str, limit: int = 5):
    """Buscar na collection."""
    await init()
    results = await client.records.query(collection=COLLECTION, query=query, limit=limit)

    print(f"\nResultados para '{query}':")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.data['title']} (score: {r.score:.4f})")

    return results


async def cleanup():
    """Limpar e fechar."""
    global client
    if client:
        try:
            await client.collections.delete(COLLECTION)
            print(f"✓ Collection '{COLLECTION}' deletada")
        except:
            pass
        await client.__aexit__(None, None, None)
        client = None
        print("✓ Client fechado")


# Helper para rodar comandos async no terminal interativo
def run(coro):
    """Helper para rodar async no terminal interativo."""
    return asyncio.run(coro)


# Auto-inicializar
print("\n" + "=" * 60)
print("  CortexDB Interactive Playground")
print("=" * 60)
print("\nFunções disponíveis:")
print("  init() - Inicializar client")
print("  create_collection() - Criar collection de teste")
print("  create_sample_data() - Criar dados de exemplo")
print("  search(query) - Buscar na collection")
print("  cleanup() - Limpar e fechar")
print("\nExemplo:")
print("  >>> await create_collection()")
print("  >>> await create_sample_data()")
print("  >>> await search('python')")
print("  >>> await cleanup()")
print("\nOu use run() para rodar sync:")
print("  >>> run(create_collection())")
print("=" * 60 + "\n")
