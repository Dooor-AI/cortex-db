"""Test de busca semântica."""

import asyncio

from cortexdb import CortexClient, FieldDefinition, FieldType

from helpers import ensure_gemini_provider


async def main():
    print("=== Teste de Busca Semântica ===\n")

    async with CortexClient("http://localhost:8000") as client:
        # 0. Configurar embedding provider
        print("0. Configurando embedding provider...")
        try:
            provider_id = await ensure_gemini_provider()
        except ValueError as e:
            print(f"   ❌ {e}")
            return
        print()

        # 1. Criar collection com vectorização
        print("1. Criando collection com vectorização...")
        try:
            await client.collections.delete("playground_search")
        except:
            pass

        schema = await client.collections.create(
            name="playground_search",
            fields=[
                FieldDefinition(name="title", type=FieldType.STRING),
                FieldDefinition(
                    name="content", type=FieldType.TEXT, vectorize=True
                ),  # Vai vetorizar
                FieldDefinition(name="category", type=FieldType.STRING),
            ],
            embedding_provider=provider_id,
        )
        print(f"   Collection: {schema.name}\n")

        # 2. Adicionar documentos de teste
        print("2. Adicionando documentos...")
        docs = [
            {
                "title": "Python Programming",
                "content": "Python is a high-level programming language known for its simplicity and readability.",
                "category": "programming",
            },
            {
                "title": "Machine Learning Basics",
                "content": "Machine learning is a subset of AI that enables computers to learn from data.",
                "category": "ai",
            },
            {
                "title": "Web Development",
                "content": "Web development involves creating websites using HTML, CSS, and JavaScript.",
                "category": "programming",
            },
            {
                "title": "Database Design",
                "content": "Database design is the process of organizing data in a structured way.",
                "category": "database",
            },
            {
                "title": "Neural Networks",
                "content": "Neural networks are computing systems inspired by biological neural networks.",
                "category": "ai",
            },
        ]

        record_ids = []
        for doc in docs:
            record = await client.records.create(collection="playground_search", data=doc)
            record_ids.append(record.id)
            print(f"   - {doc['title']}")
        print()

        # 3. Busca semântica
        print("3. Buscando: 'artificial intelligence and learning'...")
        results = await client.records.query(
            collection="playground_search",
            query="artificial intelligence and learning",
            limit=3,
        )

        print(f"   Resultados: {len(results)}\n")
        for i, result in enumerate(results, 1):
            print(f"   {i}. Score: {result.score:.4f}")
            print(f"      Title: {result.data['title']}")
            print(f"      Category: {result.data['category']}")
            print()

        # 4. Busca com filtros
        print("4. Buscando 'programming' apenas em category='programming'...")
        results = await client.records.query(
            collection="playground_search",
            query="programming languages",
            limit=5,
            filters={"category": "programming"},
        )

        print(f"   Resultados: {len(results)}\n")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.data['title']} (score: {result.score:.4f})")
        print()

        # Cleanup
        print("5. Cleanup...")
        await client.collections.delete("playground_search")
        print("   Limpo!\n")

        print("✅ Teste de busca concluído!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\nNOTA: Busca semântica requer embedding provider configurado!")
        print("Configure GEMINI_API_KEY no .env para habilitar vectorização.")
