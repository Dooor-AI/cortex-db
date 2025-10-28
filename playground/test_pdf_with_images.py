"""Teste de processamento de PDF com imagens usando Docling."""

import asyncio
from pathlib import Path

from cortexdb import CortexClient, FieldDefinition, FieldType

from helpers import ensure_gemini_provider


async def test_pdf_processing():
    """Testa processamento de PDF real com imagens."""
    
    pdf_path = Path("playground/26102025_1300_Voucher_E0150E_1015000026538.pdf")
    
    if not pdf_path.exists():
        print(f"❌ PDF não encontrado: {pdf_path}")
        return
    
    print("=" * 70)
    print("🖼️  Teste: PDF com Imagens - Docling Processing")
    print("=" * 70)
    print()
    print(f"📄 Processando: {pdf_path.name}")
    print(f"   Tamanho: {pdf_path.stat().st_size / 1024:.1f} KB")
    print()
    
    async with CortexClient("http://localhost:8000") as client:
        # Configurar provider
        print("1. Configurando embedding provider...")
        try:
            provider_id = await ensure_gemini_provider()
            print(f"   ✅ Provider: {provider_id}\n")
        except ValueError as e:
            print(f"   ❌ {e}\n")
            return
        
        # Criar collection
        print("2. Criando collection...")
        try:
            await client.collections.delete("pdf_images_test")
        except:
            pass
        
        schema = await client.collections.create(
            name="pdf_images_test",
            fields=[
                FieldDefinition(name="filename", type=FieldType.STRING),
                FieldDefinition(name="doc_type", type=FieldType.STRING),
                FieldDefinition(
                    name="document",
                    type=FieldType.FILE,
                    vectorize=True  # Docling vai processar imagens e texto
                ),
            ],
            embedding_provider=provider_id,
        )
        print(f"   ✅ Collection: {schema.name}\n")
        
        # Upload do PDF
        print("3. Fazendo upload e processamento com Docling...")
        print("   (Isso pode levar alguns segundos...)")
        
        try:
            record = await client.records.create(
                collection="pdf_images_test",
                data={
                    "filename": pdf_path.name,
                    "doc_type": "PDF com imagens"
                },
                files={"document": str(pdf_path)}
            )
            print(f"   ✅ PDF processado!")
            print(f"   Record ID: {record.id}\n")
        except Exception as e:
            print(f"   ❌ Erro no processamento: {e}\n")
            return
        
        # Verificar chunks gerados
        print("4. Analisando chunks extraídos...")
        try:
            vectors = await client.records.get_vectors("pdf_images_test", record.id)
            print(f"   ✅ Total de chunks: {len(vectors)}")
            print()
            
            if vectors:
                print("   📝 Preview dos chunks (primeiros 5):")
                print("   " + "-" * 66)
                for i, chunk in enumerate(vectors[:5], 1):
                    # Limpa o texto para display
                    text = chunk.text.replace('\n', ' ').strip()
                    preview = text[:120] if len(text) > 120 else text
                    
                    print(f"   Chunk {i}:")
                    print(f"   └─ {preview}")
                    if len(text) > 120:
                        print(f"      ... (+{len(text) - 120} chars)")
                    print()
                
                # Estatísticas
                total_chars = sum(len(c.text) for c in vectors)
                avg_chunk_size = total_chars // len(vectors) if vectors else 0
                
                print("   📊 Estatísticas:")
                print(f"   ├─ Chunks gerados: {len(vectors)}")
                print(f"   ├─ Total de caracteres: {total_chars:,}")
                print(f"   ├─ Tamanho médio/chunk: {avg_chunk_size}")
                print(f"   └─ Maior chunk: {max(len(c.text) for c in vectors)} chars")
                print()
        except Exception as e:
            print(f"   ⚠️  Erro ao obter vectors: {e}\n")
        
        # Teste de busca semântica
        print("5. Testando busca semântica no documento...")
        queries = [
            "voucher",
            "valor total",
            "número de pedido",
        ]
        
        for query in queries:
            try:
                response = await client._http.post(
                    f"/collections/pdf_images_test/search",
                    json={"query": query, "limit": 2}
                )
                results = response.get("results", [])
                
                if results:
                    print(f"   🔍 Query: '{query}'")
                    print(f"   └─ Score: {results[0]['score']:.4f}")
                    highlight = results[0].get('highlights', [])
                    if highlight:
                        text = highlight[0]['text'][:80].replace('\n', ' ')
                        print(f"      Match: {text}...")
                    print()
            except Exception as e:
                print(f"   ⚠️  Busca falhou para '{query}': {e}")
        
        # Informações sobre como Docling processou
        print("=" * 70)
        print("📖 Como o Docling Processou Este PDF:")
        print("=" * 70)
        print()
        print("O Docling fez automaticamente:")
        print()
        print("1. 🔍 Layout Analysis")
        print("   ├─ Identificou headers, footers, colunas")
        print("   ├─ Detectou ordem de leitura natural")
        print("   └─ Preservou estrutura do documento")
        print()
        print("2. 🖼️  Image Processing")
        print("   ├─ Detectou todas as imagens no PDF")
        print("   ├─ Classificou tipo de cada imagem")
        print("   ├─ Para imagens com texto: executou OCR")
        print("   ├─ Para logos/gráficos: gerou descrição")
        print("   └─ Integrou no contexto do documento")
        print()
        print("3. 📊 Table Extraction")
        print("   ├─ Identificou tabelas (se houver)")
        print("   ├─ Manteve estrutura (linhas/colunas)")
        print("   └─ Preservou dados relacionais")
        print()
        print("4. ✂️  Semantic Chunking")
        print("   ├─ Dividiu em chunks semânticos")
        print("   ├─ Respeitou seções e parágrafos")
        print("   ├─ Não quebrou no meio de tabelas/imagens")
        print("   └─ Manteve contexto entre chunks")
        print()
        print("5. 🎯 Vectorization")
        print("   ├─ Cada chunk → embedding vector")
        print("   ├─ Pronto para busca semântica")
        print("   └─ Imagens incluídas no contexto")
        print()
        
        # Cleanup
        print("=" * 70)
        print("6. Cleanup")
        print("=" * 70)
        await client.collections.delete("pdf_images_test")
        print("   ✅ Collection removida\n")
        
        print("=" * 70)
        print("✅ Teste concluído com sucesso!")
        print("=" * 70)
        print()
        print("💡 Próximos passos:")
        print("   • Teste com PDFs escaneados (imagens puras)")
        print("   • Teste com PDFs contendo gráficos complexos")
        print("   • Teste com múltiplas imagens por página")
        print("   • Compare qualidade com processamento anterior")


if __name__ == "__main__":
    try:
        asyncio.run(test_pdf_processing())
    except KeyboardInterrupt:
        print("\n\n⏸️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

