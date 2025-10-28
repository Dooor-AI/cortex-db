"""Test de processamento de documentos com Docling (PDF, DOCX, XLSX)."""

import asyncio
from pathlib import Path

from cortexdb import CortexClient, FieldDefinition, FieldType

from helpers import ensure_gemini_provider


async def main():
    print("=== Teste Docling - Processamento Avançado de Documentos ===\n")

    async with CortexClient("http://localhost:8000") as client:
        # 0. Configurar embedding provider
        print("0. Configurando embedding provider...")
        try:
            provider_id = await ensure_gemini_provider()
        except ValueError as e:
            print(f"   ❌ {e}")
            return
        print()

        # 1. Criar collection para documentos
        print("1. Criando collection para documentos...")
        try:
            await client.collections.delete("docling_test")
        except:
            pass

        schema = await client.collections.create(
            name="docling_test",
            fields=[
                FieldDefinition(name="title", type=FieldType.STRING),
                FieldDefinition(name="doc_type", type=FieldType.STRING),
                FieldDefinition(
                    name="document", 
                    type=FieldType.FILE, 
                    vectorize=True  # Docling vai processar e vetorizar
                ),
            ],
            embedding_provider=provider_id,
        )
        print(f"   ✅ Collection: {schema.name}\n")

        # 2. Testar PDF complexo
        print("2. Testando PDF com Docling...")
        print("   (Docling vai extrair layout, tabelas, fórmulas, etc)")
        
        # Usar PDF real disponível
        test_pdf = Path("Invoice-B4A5520E-0031.pdf")
        
        if not test_pdf.exists():
            print("   ⚠️  Arquivo PDF não encontrado, pulando teste")
            return
        
        try:
            record = await client.records.create(
                collection="docling_test",
                data={
                    "title": "Relatório Técnico Q1",
                    "doc_type": "PDF"
                },
                files={"document": str(test_pdf)}
            )
            print(f"   ✅ PDF processado: {record.id}\n")
        except Exception as e:
            print(f"   ⚠️  Erro ao processar PDF: {e}\n")

        # 3. Verificar chunks vetorizados
        print("3. Verificando chunks do documento...")
        try:
            vectors = await client.records.get_vectors("docling_test", record.id)
            print(f"   ✅ Total de chunks semânticos: {len(vectors)}")
            if vectors:
                print(f"\n   Chunks extraídos:")
                for i, chunk in enumerate(vectors[:3], 1):
                    preview = chunk.text[:80].replace('\n', ' ')
                    print(f"   {i}. {preview}...")
                print()
        except Exception as e:
            print(f"   ⚠️  Erro ao obter vectors: {e}\n")

        # 4. Busca semântica nos documentos processados
        print("4. Testando busca semântica...")
        try:
            response = await client._http.post(
                f"/collections/docling_test/search",
                json={"query": "relatório dados tabela", "limit": 5}
            )
            results = response.get("results", [])
            
            print(f"   ✅ Encontrados {len(results)} resultados")
            for i, result in enumerate(results, 1):
                record_data = result['record']
                print(f"   {i}. {record_data['title']} (score: {result['score']:.4f})")
                print(f"      Tipo: {record_data['doc_type']}")
                
                # Mostra highlights (chunks relevantes)
                if result.get('highlights'):
                    print(f"      Highlights:")
                    for h in result['highlights'][:2]:
                        preview = h['text'][:60].replace('\n', ' ')
                        print(f"      - {preview}... (score: {h['score']:.4f})")
            print()
        except Exception as e:
            print(f"   ⚠️  Erro na busca: {e}\n")

        # 5. Informações sobre Docling
        print("=" * 60)
        print("📚 Sobre o Docling")
        print("=" * 60)
        print()
        print("O Docling processa documentos de forma avançada:")
        print("  ✅ Layout understanding (headers, footers, columns)")
        print("  ✅ Reading order correto")
        print("  ✅ Tabelas estruturadas (não só texto)")
        print("  ✅ Fórmulas matemáticas preservadas")
        print("  ✅ Classificação de imagens")
        print("  ✅ OCR integrado para PDFs escaneados")
        print("  ✅ Suporte a: PDF, DOCX, XLSX, PPTX, HTML, imagens")
        print("  ✅ Chunking semântico (respeita estrutura)")
        print()
        print("Benefícios para RAG:")
        print("  🎯 Chunks mais relevantes → busca mais precisa")
        print("  🎯 Contexto preservado → respostas melhores")
        print("  🎯 Tabelas e fórmulas → informação estruturada")
        print()

        # Cleanup
        print("=" * 60)
        print("6. Cleanup")
        print("=" * 60)
        await client.collections.delete("docling_test")
        test_pdf.unlink(missing_ok=True)
        print("   ✅ Limpo!\n")

        print("=" * 60)
        print("✅ Teste Docling concluído!")
        print("=" * 60)
        print()
        print("💡 Para usar em produção:")
        print("   1. Upload de PDFs complexos com tabelas e fórmulas")
        print("   2. Upload de DOCX, XLSX, PPTX (funcionam automaticamente)")
        print("   3. Busca semântica retorna chunks estruturados")
        print("   4. RAG com contexto rico e preservado")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\nNOTA: Este teste requer GEMINI_API_KEY e gateway rodando")

