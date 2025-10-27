"""Tests for CortexDB client."""

import pytest

from cortexdb import CortexClient, FieldDefinition, FieldType


@pytest.mark.asyncio
async def test_client_context_manager():
    """Test client can be used as context manager."""
    async with CortexClient("http://localhost:8000") as client:
        assert client is not None
        assert client.collections is not None
        assert client.records is not None


@pytest.mark.asyncio
async def test_client_close():
    """Test client can be closed manually."""
    client = CortexClient("http://localhost:8000")
    await client.close()
    # Should not raise


@pytest.mark.asyncio
async def test_healthcheck():
    """Test healthcheck endpoint."""
    async with CortexClient("http://localhost:8000") as client:
        # Assuming local server is running
        is_healthy = await client.healthcheck()
        assert isinstance(is_healthy, bool)


@pytest.mark.asyncio
async def test_create_and_list_collections():
    """Test creating and listing collections."""
    async with CortexClient("http://localhost:8000") as client:
        # Create collection
        schema = await client.collections.create(
            name="test_collection",
            fields=[
                FieldDefinition(name="title", type=FieldType.STRING),
                FieldDefinition(name="content", type=FieldType.TEXT, vectorize=True),
            ],
        )

        assert schema.name == "test_collection"
        assert len(schema.fields) == 2

        # List collections
        collections = await client.collections.list()
        assert any(c.name == "test_collection" for c in collections)

        # Cleanup
        await client.collections.delete("test_collection")


@pytest.mark.asyncio
async def test_create_and_get_record():
    """Test creating and retrieving a record."""
    async with CortexClient("http://localhost:8000") as client:
        # Create collection
        await client.collections.create(
            name="test_records",
            fields=[
                FieldDefinition(name="title", type=FieldType.STRING),
                FieldDefinition(name="content", type=FieldType.TEXT, vectorize=True),
            ],
        )

        # Create record
        record = await client.records.create(
            collection="test_records",
            data={"title": "Test", "content": "Hello World"},
        )

        assert record.id is not None
        assert record.data["title"] == "Test"

        # Get record
        fetched = await client.records.get("test_records", record.id)
        assert fetched.id == record.id
        assert fetched.data["title"] == "Test"

        # Cleanup
        await client.collections.delete("test_records")


@pytest.mark.asyncio
async def test_query_records():
    """Test semantic search query."""
    async with CortexClient("http://localhost:8000") as client:
        # Create collection
        await client.collections.create(
            name="test_search",
            fields=[
                FieldDefinition(name="title", type=FieldType.STRING),
                FieldDefinition(name="content", type=FieldType.TEXT, vectorize=True),
            ],
        )

        # Create records
        await client.records.create(
            collection="test_search",
            data={"title": "ML", "content": "Machine learning is amazing"},
        )
        await client.records.create(
            collection="test_search",
            data={"title": "DL", "content": "Deep learning uses neural networks"},
        )

        # Query
        results = await client.records.query(
            collection="test_search",
            query="artificial intelligence",
            limit=10,
        )

        assert len(results) >= 0
        for result in results:
            assert result.id is not None
            assert result.score >= 0

        # Cleanup
        await client.collections.delete("test_search")
