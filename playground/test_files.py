"""Test de upload e download de arquivos."""

import asyncio
from pathlib import Path

from cortexdb import CortexClient, FieldDefinition, FieldType


async def main():
    print("=== Teste de Files - Upload/Download ===\n")

    async with CortexClient("http://localhost:8000") as client:
        # 1. Criar collection com file field
        print("1. Criando collection com file field...")
        try:
            await client.collections.delete("playground_files")
        except:
            pass

        schema = await client.collections.create(
            name="playground_files",
            fields=[
                FieldDefinition(name="title", type=FieldType.STRING),
                FieldDefinition(
                    name="document", type=FieldType.FILE, vectorize=False
                ),  # Apenas armazenar o arquivo sem vectorização
            ],
        )
        print(f"   Collection: {schema.name}\n")

        # 2. Criar arquivo de teste
        print("2. Criando arquivo de teste...")
        test_file = Path("playground/sample_files/test.txt")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Este é um arquivo de teste para o CortexDB.\nTeste de upload e download.\n")
        print(f"   Arquivo criado: {test_file}\n")

        # 3. Upload do arquivo
        print("3. Fazendo upload do arquivo...")
        record = await client.records.create(
            collection="playground_files",
            data={"title": "Documento de Teste"},
            files={"document": str(test_file)},
        )
        print(f"   Record ID: {record.id}")
        print(f"   Title: {record.data['title']}\n")

        # 4. Download do arquivo
        print("4. Fazendo download do arquivo...")
        download_path = Path("playground/sample_files/downloaded.txt")
        await client.records.download_file(
            collection="playground_files",
            record_id=record.id,
            field_name="document",
            output_path=str(download_path),
        )
        print(f"   Arquivo baixado: {download_path}")

        # Verificar conteúdo
        downloaded_content = download_path.read_text()
        print(f"   Conteúdo: {downloaded_content[:50]}...\n")

        # 5. Download como bytes
        print("5. Download direto como bytes...")
        file_bytes = await client.records.download_file(
            collection="playground_files", record_id=record.id, field_name="document"
        )
        print(f"   Tamanho: {len(file_bytes)} bytes")
        print(f"   Preview: {file_bytes[:50]}\n")

        # 6. Verificar vectors (se tiver embedding configurado)
        print("6. Verificando vectors extraídos...")
        try:
            vectors = await client.records.get_vectors("playground_files", record.id)
            print(f"   Total de chunks: {len(vectors)}")
            if vectors:
                print(f"   Chunk 0: {vectors[0].text[:100]}...")
        except Exception as e:
            print(f"   (Sem vectors - embeddings não configurados ou arquivo não vetorizável)")
        print()

        # Cleanup
        print("7. Cleanup...")
        await client.collections.delete("playground_files")
        test_file.unlink()
        download_path.unlink()
        print("   Limpo!\n")

        print("✅ Teste de files concluído!")


if __name__ == "__main__":
    asyncio.run(main())
