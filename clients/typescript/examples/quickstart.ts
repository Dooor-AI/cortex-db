/** CortexDB Quickstart Example */

import { CortexClient, FieldType, StoreLocation } from "../src";

async function main() {
  console.log("=== CortexDB TypeScript SDK Quickstart ===\n");

  // Initialize client
  const client = new CortexClient({
    baseUrl: "http://localhost:8000",
  });

  try {
    // Check health
    console.log("1. Health Check");
    const isHealthy = await client.healthcheck();
    console.log(`   ✓ Health check: ${isHealthy ? "OK" : "FAILED"}\n`);

    // Clean up if exists
    try {
      await client.collections.delete("documents");
    } catch (e) {
      // Ignore if doesn't exist
    }

    // Create a collection
    console.log("2. Creating Collection");
    const collection = await client.collections.create("documents", [
      {
        name: "title",
        type: "string" as FieldType,
      },
      {
        name: "content",
        type: "string" as FieldType,
        vectorize: false, // Set to true with embedding_provider for semantic search
      },
      {
        name: "year",
        type: "number" as FieldType,
        store_in: [StoreLocation.POSTGRES, StoreLocation.QDRANT_PAYLOAD],
      },
    ]);
    console.log(`   ✓ Created collection: ${collection.name}\n`);

    // List collections
    console.log("3. Listing Collections");
    const collections = await client.collections.list();
    console.log(`   ✓ Total collections: ${collections.length}\n`);

    // Create records
    console.log("4. Creating Records");
    
    const record1 = await client.records.create("documents", {
      title: "Introduction to AI",
      content: "Artificial Intelligence is transforming the world...",
      year: 2024,
    });
    console.log(`   ✓ Created record 1: ${record1.id}`);

    const record2 = await client.records.create("documents", {
      title: "Machine Learning Basics",
      content: "Machine learning is a subset of AI...",
      year: 2023,
    });
    console.log(`   ✓ Created record 2: ${record2.id}\n`);

    // Get a record
    console.log("5. Fetching Record");
    const fetched = await client.records.get("documents", record1.id);
    console.log(`   ✓ Fetched: ${JSON.stringify(fetched.data, null, 2)}\n`);

    // List all records
    console.log("6. Listing Records");
    const allRecords = await client.records.list("documents", { limit: 10 });
    console.log(`   ✓ Total records: ${allRecords.total}\n`);

    // Update a record
    console.log("7. Updating Record");
    const updated = await client.records.update("documents", record1.id, {
      title: "Introduction to Artificial Intelligence",
      content: "AI is revolutionizing technology...",
      year: 2024,
    });
    console.log(`   ✓ Updated record: ${updated.id}\n`);

    // Delete a record
    console.log("8. Deleting Record");
    await client.records.delete("documents", record2.id);
    console.log(`   ✓ Deleted record: ${record2.id}\n`);

    // List records after deletion
    const remainingRecords = await client.records.list("documents");
    console.log(`   ✓ Remaining records: ${remainingRecords.total}\n`);

    // Cleanup
    console.log("9. Cleanup");
    await client.collections.delete("documents");
    console.log("   ✓ Collection deleted\n");

    console.log("✅ Quickstart completed successfully!");
  } catch (error) {
    console.error("❌ Error:", error);
    throw error;
  } finally {
    await client.close();
  }
}

// Run the example
main().catch(console.error);

