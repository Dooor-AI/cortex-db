"""Teste com embedding provider configurado."""

import asyncio

from cortexdb import CortexClient, FieldDefinition, FieldType


async def main():
    print("=== Teste com Embedding Provider ===\n")

    async with CortexClient("http://localhost:8000") as client:
        # Este teste requer que você tenha configurado um embedding provider
        # no gateway (via /settings/embeddings)
        
        # Para rodar este teste:
        # 1. Configure um provider: POST /settings/embeddings/providers
        # 2. Use o ID do provider abaixo
        PROVIDER_ID = "seu-provider-id-aqui"  # Substitua pelo ID real
        
        print("⚠️  ATENÇÃO: Este teste requer provider configurado!")
        print(f"   Configure um provider e atualize PROVIDER_ID no código")
        print()

        # 1. Criar collection com vectorização
        print("1. Criando collection com vectorização...")
        try:
            # Tenta deletar collection anterior
            await client.collections.delete("playground_vectorized")
        except:
            pass

        try:
            schema = await client.collections.create(
                name="playground_vectorized",
                fields=[
                    FieldDefinition(name="title", type=FieldType.STRING),
                    FieldDefinition(
                        name="content", type=FieldType.TEXT, vectorize=True
                    ),
                ],
                embedding_provider=PROVIDER_ID,
            )
            print(f"   ✅ Collection criada: {schema.name}\n")

            # 2. Criar record com conteúdo que será vetorizado
            print("2. Criando record com conteúdo vetorizável...")
            record = await client.records.create(
                collection="playground_vectorized",
                data={
                    "title": "Introdução ao Python",
                    "content": "Python é uma linguagem de programação versátil e poderosa.",
                },
            )
            print(f"   ✅ Record ID: {record.id}\n")

            # 3. Fazer busca semântica
            print("3. Fazendo busca semântica...")
            try:
                results = await client.search.semantic_search(
                    collection="playground_vectorized",
                    query="programming language",
                    limit=5,
                )
                print(f"   ✅ Encontrados {len(results)} resultados")
                if results:
                    print(f"   Primeiro resultado: {results[0].data.get('title')}")
            except Exception as e:
                print(f"   ⚠️  Busca falhou: {e}")

            print()

            # 4. Verificar vectors
            print("4. Verificando vectors...")
            try:
                vectors = await client.records.get_vectors("playground_vectorized", record.id)
                print(f"   ✅ Total de chunks: {len(vectors)}")
                if vectors:
                    print(f"   Primeiro chunk: {vectors[0].text[:100]}...")
            except Exception as e:
                print(f"   ⚠️  Falha ao obter vectors: {e}")

            print()

            # 5. Cleanup
            print("5. Limpando...")
            await client.collections.delete("playground_vectorized")
            print("   ✅ Limpo!\n")

            print("✅ Teste com provider concluído!")

        except ValueError as e:
            if "embedding_provider" in str(e):
                print(f"   ❌ Erro: {e}")
                print()
                print("💡 SOLUÇÃO:")
                print("   1. Configure um embedding provider no gateway")
                print("   2. Use curl para configurar ou acesse /settings/embeddings")
                print("   3. Atualize PROVIDER_ID com o ID real do provider")
            else:
                raise


if __name__ == "__main__":
    asyncio.run(main())

