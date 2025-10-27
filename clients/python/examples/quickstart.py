"""CortexDB Quickstart Example."""

import asyncio

from cortexdb import CortexClient, FieldDefinition, FieldType, StoreLocation


async def main():
    """Quickstart example demonstrating basic CortexDB operations."""

    # Initialize client
    async with CortexClient("http://localhost:8000") as client:
        print("✓ Connected to CortexDB")

        # Check health
        is_healthy = await client.healthcheck()
        print(f"✓ Health check: {'OK' if is_healthy else 'FAILED'}")

        # Create a collection
        print("\n--- Creating Collection ---")
        schema = await client.collections.create(
            name="documents",
            fields=[
                FieldDefinition(
                    name="title",
                    type=FieldType.STRING,
                ),
                FieldDefinition(
                    name="content",
                    type=FieldType.TEXT,
                    vectorize=True,  # Enable vectorization for semantic search
                ),
                FieldDefinition(
                    name="year",
                    type=FieldType.INT,
                    store_in=[StoreLocation.POSTGRES, StoreLocation.QDRANT_PAYLOAD],
                ),
            ],
        )
        print(f"✓ Created collection: {schema.name}")

        # List collections
        collections = await client.collections.list()
        print(f"✓ Total collections: {len(collections)}")

        # Create records
        print("\n--- Creating Records ---")
        records = []

        record1 = await client.records.create(
            collection="documents",
            data={
                "title": "Introduction to Machine Learning",
                "content": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience.",
                "year": 2023,
            },
        )
        records.append(record1)
        print(f"✓ Created record: {record1.id}")

        record2 = await client.records.create(
            collection="documents",
            data={
                "title": "Deep Learning Fundamentals",
                "content": "Deep learning uses neural networks with multiple layers to progressively extract higher-level features from raw input.",
                "year": 2024,
            },
        )
        records.append(record2)
        print(f"✓ Created record: {record2.id}")

        record3 = await client.records.create(
            collection="documents",
            data={
                "title": "Natural Language Processing",
                "content": "NLP enables computers to understand, interpret, and generate human language in a valuable way.",
                "year": 2024,
            },
        )
        records.append(record3)
        print(f"✓ Created record: {record3.id}")

        # Semantic search
        print("\n--- Semantic Search ---")
        results = await client.records.query(
            collection="documents",
            query="neural networks and AI",
            limit=3,
        )

        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result.score:.4f}")
            print(f"   Title: {result.data['title']}")
            print(f"   Year: {result.data['year']}")

        # Search with filters
        print("\n--- Filtered Search ---")
        results = await client.records.query(
            collection="documents",
            query="machine learning",
            limit=10,
            filters={"year": {"$gte": 2024}},  # Only 2024 and newer
        )

        print(f"Found {len(results)} results from 2024+:")
        for result in results:
            print(f"  - {result.data['title']} ({result.data['year']})")

        # Get record by ID
        print("\n--- Get Record ---")
        fetched = await client.records.get("documents", record1.id)
        print(f"✓ Fetched record: {fetched.data['title']}")

        # Get vector chunks
        print("\n--- Vector Chunks ---")
        chunks = await client.records.get_vectors("documents", record1.id)
        print(f"✓ Vector chunks: {len(chunks)}")
        for chunk in chunks:
            print(f"  - Field: {chunk.field}, Index: {chunk.chunk_index}")
            print(f"    Text: {chunk.text[:100]}...")

        # Update record
        print("\n--- Update Record ---")
        updated = await client.records.update(
            collection="documents",
            record_id=record1.id,
            data={"year": 2025},
        )
        print(f"✓ Updated record year to: {updated.data['year']}")

        # Delete record
        print("\n--- Delete Record ---")
        await client.records.delete("documents", record3.id)
        print(f"✓ Deleted record: {record3.id}")

        # Cleanup
        print("\n--- Cleanup ---")
        await client.collections.delete("documents")
        print("✓ Deleted collection: documents")

        print("\n✅ Quickstart completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
