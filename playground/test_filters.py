"""Test de filtros avançados na busca."""

import asyncio

from cortexdb import CortexClient, FieldDefinition, FieldType

from helpers import ensure_gemini_provider


async def main():
    print("=== Teste de Filtros Avançados ===\n")

    async with CortexClient("http://localhost:8000") as client:
        # 0. Configurar embedding provider
        print("0. Configurando embedding provider...")
        try:
            provider_id = await ensure_gemini_provider()
        except ValueError as e:
            print(f"   ❌ {e}")
            return
        print()

        # 1. Criar collection
        print("1. Criando collection...")
        try:
            await client.collections.delete("playground_filters")
        except:
            pass

        schema = await client.collections.create(
            name="playground_filters",
            fields=[
                FieldDefinition(name="title", type=FieldType.STRING),
                FieldDefinition(name="content", type=FieldType.TEXT, vectorize=True),
                FieldDefinition(name="year", type=FieldType.INT),
                FieldDefinition(name="price", type=FieldType.FLOAT),
                FieldDefinition(name="available", type=FieldType.BOOLEAN),
                FieldDefinition(name="category", type=FieldType.STRING),
            ],
            embedding_provider=provider_id,
        )
        print(f"   Collection: {schema.name}\n")

        # 2. Adicionar dados
        print("2. Adicionando dados de teste...")
        data = [
            {
                "title": "Python Course 2023",
                "content": "Learn Python programming from basics to advanced",
                "year": 2023,
                "price": 49.99,
                "available": True,
                "category": "programming",
            },
            {
                "title": "Machine Learning 2024",
                "content": "Deep dive into machine learning algorithms",
                "year": 2024,
                "price": 79.99,
                "available": True,
                "category": "ai",
            },
            {
                "title": "Web Dev Basics 2022",
                "content": "HTML, CSS and JavaScript fundamentals",
                "year": 2022,
                "price": 29.99,
                "available": False,
                "category": "programming",
            },
            {
                "title": "Data Science 2024",
                "content": "Statistics and data analysis with Python",
                "year": 2024,
                "price": 99.99,
                "available": True,
                "category": "data",
            },
            {
                "title": "DevOps 2023",
                "content": "Docker, Kubernetes and CI/CD pipelines",
                "year": 2023,
                "price": 59.99,
                "available": True,
                "category": "devops",
            },
        ]

        for item in data:
            await client.records.create(collection="playground_filters", data=item)
            print(f"   - {item['title']}")
        print()

        # 3. Testes de filtros
        print("3. Teste 1: Apenas cursos de 2024...")
        results = await client.records.query(
            collection="playground_filters",
            query="programming and data",
            limit=10,
            filters={"year": 2024},
        )
        print(f"   Resultados: {len(results)}")
        for r in results:
            print(f"   - {r.data['title']} ({r.data['year']})")
        print()

        print("4. Teste 2: Preço menor que $60...")
        results = await client.records.query(
            collection="playground_filters",
            query="course learning",
            limit=10,
            filters={"price": {"$lt": 60}},
        )
        print(f"   Resultados: {len(results)}")
        for r in results:
            print(f"   - {r.data['title']} (R$ {r.data['price']})")
        print()

        print("5. Teste 3: Ano >= 2023 E disponível...")
        results = await client.records.query(
            collection="playground_filters",
            query="technology",
            limit=10,
            filters={"year": {"$gte": 2023}, "available": True},
        )
        print(f"   Resultados: {len(results)}")
        for r in results:
            print(f"   - {r.data['title']} ({r.data['year']}, available: {r.data['available']})")
        print()

        print("6. Teste 4: Categoria 'programming'...")
        results = await client.records.query(
            collection="playground_filters",
            query="coding",
            limit=10,
            filters={"category": "programming"},
        )
        print(f"   Resultados: {len(results)}")
        for r in results:
            print(f"   - {r.data['title']} ({r.data['category']})")
        print()

        print("7. Teste 5: Preço entre $40 e $80...")
        results = await client.records.query(
            collection="playground_filters",
            query="advanced",
            limit=10,
            filters={"price": {"$gte": 40, "$lte": 80}},
        )
        print(f"   Resultados: {len(results)}")
        for r in results:
            print(f"   - {r.data['title']} (R$ {r.data['price']})")
        print()

        # Cleanup
        print("8. Cleanup...")
        await client.collections.delete("playground_filters")
        print("   Limpo!\n")

        print("✅ Teste de filtros concluído!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\nNOTA: Filtros requerem embedding provider para busca semântica!")
