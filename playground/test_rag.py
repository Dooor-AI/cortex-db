"""Test de RAG - Busca semântica vetorial."""

import asyncio

from cortexdb import CortexClient, FieldDefinition, FieldType

from helpers import ensure_gemini_provider


async def main():
    print("=== Teste de RAG - Retrieval Augmented Generation ===\n")

    async with CortexClient("http://localhost:8000") as client:
        # 0. Configurar embedding provider
        print("0. Configurando embedding provider...")
        try:
            provider_id = await ensure_gemini_provider()
        except ValueError as e:
            print(f"   ❌ {e}")
            return
        print()

        # 1. Criar knowledge base com documentos vetorizados
        print("1. Criando knowledge base...")
        try:
            await client.collections.delete("knowledge_base")
        except:
            pass

        schema = await client.collections.create(
            name="knowledge_base",
            fields=[
                FieldDefinition(name="title", type=FieldType.STRING),
                FieldDefinition(
                    name="content", 
                    type=FieldType.TEXT, 
                    vectorize=True  # Vetoriza para busca semântica
                ),
                FieldDefinition(name="source", type=FieldType.STRING),
            ],
            embedding_provider=provider_id,
        )
        print(f"   ✅ Knowledge base criada: {schema.name}\n")

        # 2. Adicionar documentos de conhecimento
        print("2. Adicionando documentos à knowledge base...")
        documents = [
            {
                "title": "O que é Python?",
                "content": """Python é uma linguagem de programação de alto nível, interpretada e de propósito geral.
                Foi criada por Guido van Rossum e lançada em 1991. Python é conhecida por sua sintaxe clara e legível,
                o que a torna ideal para iniciantes. É amplamente utilizada em desenvolvimento web, ciência de dados,
                machine learning, automação e muito mais.""",
                "source": "docs/python.md",
            },
            {
                "title": "Machine Learning com Python",
                "content": """Machine Learning é um subcampo da inteligência artificial que permite aos computadores
                aprenderem com dados sem serem explicitamente programados. Python é a linguagem mais popular para ML,
                com bibliotecas como scikit-learn, TensorFlow e PyTorch. Essas ferramentas facilitam a criação de
                modelos preditivos, classificação e análise de dados.""",
                "source": "docs/ml.md",
            },
            {
                "title": "Web Development com FastAPI",
                "content": """FastAPI é um framework web moderno e rápido para construir APIs com Python 3.7+.
                Ele é baseado em type hints do Python e oferece validação automática, documentação interativa
                e alto desempenho. FastAPI é ideal para criar APIs RESTful e microsserviços escaláveis.""",
                "source": "docs/fastapi.md",
            },
            {
                "title": "Banco de Dados PostgreSQL",
                "content": """PostgreSQL é um sistema de gerenciamento de banco de dados relacional open-source.
                É conhecido por sua confiabilidade, robustez de recursos e conformidade com SQL. PostgreSQL suporta
                dados relacionais e não-relacionais (JSON), além de recursos avançados como índices, transações
                ACID e replicação.""",
                "source": "docs/postgres.md",
            },
            {
                "title": "Ciência de Dados",
                "content": """Ciência de dados é a área que combina estatística, programação e conhecimento de domínio
                para extrair insights de dados. Python é a principal ferramenta, com bibliotecas como Pandas para
                manipulação de dados, NumPy para computação numérica, Matplotlib para visualização e Jupyter notebooks
                para análise interativa.""",
                "source": "docs/data-science.md",
            },
        ]

        record_ids = []
        for doc in documents:
            record = await client.records.create(
                collection="knowledge_base", 
                data=doc
            )
            record_ids.append(record.id)
            print(f"   ✅ {doc['title']}")
        print(f"\n   Total: {len(record_ids)} documentos adicionados\n")

        # 3. RAG - Fazer perguntas e recuperar conhecimento relevante
        print("=" * 60)
        print("3. RAG - Busca Semântica Vetorial")
        print("=" * 60)
        
        queries = [
            "Como começar a programar?",
            "Quais ferramentas usar para inteligência artificial?",
            "Como criar uma API REST?",
            "Qual banco de dados usar?",
        ]

        for i, query in enumerate(queries, 1):
            print(f"\n📝 Pergunta {i}: '{query}'")
            print("-" * 60)
            
            # Busca semântica vetorial
            # Usar o endpoint /search diretamente pois query() usa endpoint errado
            response = await client._http.post(
                f"/collections/knowledge_base/search",
                json={"query": query, "limit": 2}
            )
            results = response.get("results", [])
            
            if results:
                print(f"✅ Encontrados {len(results)} resultados relevantes:\n")
                for j, result in enumerate(results, 1):
                    record = result['record']
                    print(f"   {j}. {record['title']} (score: {result['score']:.4f})")
                    print(f"      Fonte: {record['source']}")
                    # Mostra preview do conteúdo
                    content_preview = record['content'][:150].replace('\n', ' ')
                    print(f"      Preview: {content_preview}...")
                    print()
            else:
                print("   ⚠️  Nenhum resultado encontrado\n")

        # 4. Verificar vectors dos chunks
        print("=" * 60)
        print("4. Verificando vectorização dos documentos")
        print("=" * 60)
        print()
        
        # Pegar o primeiro documento
        first_doc_id = record_ids[0]
        vectors = await client.records.get_vectors("knowledge_base", first_doc_id)
        
        print(f"📄 Documento: {documents[0]['title']}")
        print(f"   Total de chunks vetorizados: {len(vectors)}")
        if vectors:
            # Mostra chunks (não mostramos o vetor pois é muito grande)
            print(f"\n   Chunks:")
            for i, chunk in enumerate(vectors[:3], 1):  # Mostra só 3 primeiros
                chunk_preview = chunk.text[:80].replace('\n', ' ')
                print(f"   {i}. {chunk_preview}...")
            print(f"\n   💡 Cada chunk foi convertido em vetor para busca semântica")
        print()

        # 5. Busca com filtros
        print("=" * 60)
        print("5. RAG com Filtros - Busca apenas em fonte específica")
        print("=" * 60)
        print()
        
        query = "aprendizado de máquina"
        print(f"📝 Pergunta: '{query}' (filtro: source contém 'ml')")
        print("-" * 60)
        
        response = await client._http.post(
            f"/collections/knowledge_base/search",
            json={"query": query, "limit": 3, "filters": {"source": {"$like": "%ml%"}}}
        )
        results = response.get("results", [])
        
        print(f"✅ Resultados filtrados: {len(results)}\n")
        for i, result in enumerate(results, 1):
            record = result['record']
            print(f"   {i}. {record['title']} (score: {result['score']:.4f})")
            print(f"      Fonte: {record['source']}\n")

        # 6. Comparação: busca vs filtro exato
        print("=" * 60)
        print("6. Comparação: Busca Semântica vs Busca Exata")
        print("=" * 60)
        print()
        
        print("🔍 Busca semântica: 'bibliotecas para análise de dados'")
        response = await client._http.post(
            f"/collections/knowledge_base/search",
            json={"query": "bibliotecas para análise de dados", "limit": 2}
        )
        semantic_results = response.get("results", [])
        print(f"   Resultados por similaridade vetorial: {len(semantic_results)}")
        for result in semantic_results:
            record = result['record']
            print(f"   - {record['title']} (score: {result['score']:.4f})")
        print()
        
        print("🔍 Busca por filtro: title contém 'Ciência'")
        # Usando endpoint de query com filtro  
        response = await client._http.post(
            f"/collections/knowledge_base/query",
            json={"filters": {"title": {"$like": "%Ciência%"}}, "limit": 10}
        )
        exact_results = response.get("results", [])
        print(f"   Resultados por filtro: {len(exact_results)}")
        for result in exact_results:
            print(f"   - {result['title']}")
        print()

        # Cleanup
        print("=" * 60)
        print("7. Cleanup")
        print("=" * 60)
        await client.collections.delete("knowledge_base")
        print("   ✅ Knowledge base removida\n")

        print("=" * 60)
        print("✅ Teste de RAG concluído com sucesso!")
        print("=" * 60)
        print("\n💡 Resumo:")
        print("   - Documentos vetorizados automaticamente")
        print("   - Busca semântica funciona por similaridade vetorial")
        print("   - Filtros podem ser combinados com busca semântica")
        print("   - RAG permite recuperar conhecimento relevante para LLMs")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\nNOTA: Este teste requer GEMINI_API_KEY configurada no .env")

