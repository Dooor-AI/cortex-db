"""Example: Uploading files with CortexDB."""

import asyncio
from pathlib import Path

from cortexdb import CortexClient, FieldDefinition, FieldType


async def main():
    """Example demonstrating file upload and vectorization."""

    async with CortexClient("http://localhost:8000") as client:
        print("✓ Connected to CortexDB\n")

        # Create collection with file field
        print("--- Creating Collection ---")
        schema = await client.collections.create(
            name="documents_with_files",
            fields=[
                FieldDefinition(name="title", type=FieldType.STRING),
                FieldDefinition(name="description", type=FieldType.TEXT, vectorize=True),
                FieldDefinition(
                    name="document",
                    type=FieldType.FILE,
                    vectorize=True,  # Extract text and vectorize
                ),
            ],
        )
        print(f"✓ Created collection: {schema.name}\n")

        # Upload a file
        print("--- Uploading File ---")
        record = await client.records.create(
            collection="documents_with_files",
            data={
                "title": "Annual Report 2024",
                "description": "Company annual financial report for fiscal year 2024",
            },
            files={
                "document": Path("/path/to/your/file.pdf"),  # Replace with actual path
                # or use bytes: "document": b"file content..."
            },
        )
        print(f"✓ Uploaded file, record ID: {record.id}\n")

        # Get the record
        fetched = await client.records.get("documents_with_files", record.id)
        print(f"✓ Fetched record: {fetched.data['title']}")
        print(f"  File path: {fetched.data.get('document', 'N/A')}\n")

        # Get vectorized chunks from the file
        print("--- Vector Chunks from PDF ---")
        chunks = await client.records.get_vectors("documents_with_files", record.id)
        print(f"✓ Extracted {len(chunks)} chunks\n")

        for i, chunk in enumerate(chunks[:3], 1):  # Show first 3 chunks
            print(f"Chunk {i}:")
            print(f"  Field: {chunk.field}")
            print(f"  Index: {chunk.chunk_index}")
            print(f"  Text: {chunk.text[:150]}...\n")

        # Search across file content
        print("--- Semantic Search in Files ---")
        results = await client.records.query(
            collection="documents_with_files",
            query="financial performance revenue",
            limit=5,
        )

        print(f"Found {len(results)} results:")
        for result in results:
            print(f"  - {result.data['title']} (score: {result.score:.4f})")

        # Update file
        print("\n--- Updating File ---")
        updated = await client.records.update(
            collection="documents_with_files",
            record_id=record.id,
            data={"description": "Updated description"},
            files={"document": Path("/path/to/new/file.pdf")},
        )
        print(f"✓ Updated record with new file\n")

        # Cleanup
        print("--- Cleanup ---")
        await client.collections.delete("documents_with_files")
        print("✓ Deleted collection\n")

        print("✅ File upload example completed!")


if __name__ == "__main__":
    asyncio.run(main())
