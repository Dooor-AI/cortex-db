"""Simple test to verify SDK works with local gateway."""

import asyncio

from cortexdb import CortexClient, FieldDefinition, FieldType


async def main():
    print("🚀 Testing CortexDB Python SDK\n")

    async with CortexClient("http://localhost:8000") as client:
        # 1. Health check
        print("1. Health Check...")
        is_healthy = await client.healthcheck()
        print(f"   ✓ Gateway is {'healthy' if is_healthy else 'unhealthy'}\n")

        if not is_healthy:
            print("❌ Gateway is not running. Start it with: docker compose up")
            return

        # 2. List existing collections
        print("2. Listing Collections...")
        collections = await client.collections.list()
        print(f"   ✓ Found {len(collections)} collections")
        for col in collections:
            print(f"     - {col.name}")
        print()

        # 3. Create a test collection (no vectorization to avoid embedding provider requirement)
        collection_name = "sdk_test"
        print(f"3. Creating Collection '{collection_name}'...")

        # Delete if exists
        try:
            await client.collections.delete(collection_name)
            print(f"   ⚠ Deleted existing collection\n")
        except Exception:
            pass  # Collection doesn't exist, that's fine

        schema = await client.collections.create(
            name=collection_name,
            fields=[
                FieldDefinition(name="title", type=FieldType.STRING),
                FieldDefinition(name="content", type=FieldType.TEXT),
                FieldDefinition(name="count", type=FieldType.INT),
            ],
        )
        print(f"   ✓ Created collection: {schema.name}")
        print(f"     Fields: {', '.join(f.name for f in schema.fields)}\n")

        # 4. Create a record
        print("4. Creating Record...")
        record = await client.records.create(
            collection=collection_name,
            data={
                "title": "SDK Test Document",
                "content": "This is a test document created by the CortexDB Python SDK.",
                "count": 42,
            },
        )
        print(f"   ✓ Created record: {record.id}")
        print(f"     Title: {record.data.get('title')}")
        print(f"     Count: {record.data.get('count')}\n")

        # 5. Get the record
        print("5. Fetching Record...")
        fetched = await client.records.get(collection_name, record.id)
        print(f"   ✓ Fetched record: {fetched.id}")
        print(f"     Content: {fetched.data.get('content')[:50]}...\n")

        # 6. Update the record
        print("6. Updating Record...")
        updated = await client.records.update(
            collection=collection_name,
            record_id=record.id,
            data={"content": "Updated content from SDK test", "count": 100},
        )
        print(f"   ✓ Updated record: {updated.id}")
        print(f"     New count: {updated.data.get('count')}\n")

        # 7. Delete the record
        print("7. Deleting Record...")
        await client.records.delete(collection_name, record.id)
        print(f"   ✓ Deleted record: {record.id}\n")

        # 8. Cleanup - delete collection
        print("8. Cleanup...")
        try:
            await client.collections.delete(collection_name)
            print(f"   ✓ Deleted collection: {collection_name}\n")
        except Exception as e:
            print(f"   ⚠ Cleanup failed: {e}\n")

        print("✅ All tests passed! SDK is working correctly.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
