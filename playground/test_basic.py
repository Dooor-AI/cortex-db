"""Test básico - CRUD de collections e records."""

import asyncio

from cortexdb import CortexClient, FieldDefinition, FieldType


async def main():
    print("=== Teste Básico - CRUD ===\n")

    async with CortexClient("http://localhost:8000") as client:
        # 1. Health check
        print("1. Health check...")
        healthy = await client.healthcheck()
        print(f"   Gateway: {'OK' if healthy else 'ERRO'}\n")

        # 2. Criar collection
        print("2. Criando collection 'playground_test'...")
        try:
            await client.collections.delete("playground_test")
            print("   (deletou collection antiga)")
        except:
            pass

        schema = await client.collections.create(
            name="playground_test",
            fields=[
                FieldDefinition(name="title", type=FieldType.STRING),
                FieldDefinition(name="description", type=FieldType.TEXT),
                FieldDefinition(name="price", type=FieldType.FLOAT),
                FieldDefinition(name="stock", type=FieldType.INT),
                FieldDefinition(name="active", type=FieldType.BOOLEAN),
            ],
        )
        print(f"   Collection criada: {schema.name}")
        print(f"   Fields: {[f.name for f in schema.fields]}\n")

        # 3. Criar records
        print("3. Criando records...")
        records = []
        for i in range(5):
            record = await client.records.create(
                collection="playground_test",
                data={
                    "title": f"Produto {i+1}",
                    "description": f"Descrição do produto {i+1}",
                    "price": 10.99 * (i + 1),
                    "stock": 100 - (i * 10),
                    "active": i % 2 == 0,
                },
            )
            records.append(record)
            print(f"   Record {i+1}: {record.id}")
        print()

        # 4. Ler record
        print("4. Lendo record...")
        fetched = await client.records.get("playground_test", records[0].id)
        print(f"   ID: {fetched.id}")
        print(f"   Title: {fetched.data['title']}")
        print(f"   Price: R$ {fetched.data['price']:.2f}\n")

        # 5. Atualizar record
        print("5. Atualizando record...")
        updated = await client.records.update(
            collection="playground_test",
            record_id=records[0].id,
            data={"price": 99.99, "stock": 50},
        )
        print(f"   Novo price: R$ {updated.data['price']:.2f}")
        print(f"   Novo stock: {updated.data['stock']}\n")

        # 6. Deletar record
        print("6. Deletando record...")
        await client.records.delete("playground_test", records[-1].id)
        print(f"   Record deletado: {records[-1].id}\n")

        # 7. Listar collections
        print("7. Listando collections...")
        collections = await client.collections.list()
        print(f"   Total: {len(collections)}")
        for col in collections:
            print(f"   - {col.name}")
        print()

        # Cleanup
        print("8. Cleanup...")
        await client.collections.delete("playground_test")
        print("   Collection deletada\n")

        print("✅ Teste concluído com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
