/** Basic example using CortexDB TypeScript SDK */

import { CortexClient } from "../src";

async function main() {
  const client = new CortexClient({
    baseUrl: "http://localhost:8000",
  });

  try {
    console.log("🚀 Starting CortexDB TypeScript SDK example\n");

    // Check health
    console.log("1. Checking health...");
    const health = await client.health();
    console.log("   ✅ Status:", health.status);

    // List collections
    console.log("\n2. Listing collections...");
    const collections = await client.collections.list();
    console.log(`   ✅ Found ${collections.length} collections`);

    // Create a collection if it doesn't exist
    console.log("\n3. Creating collection 'typescript_test'...");
    try {
      await client.collections.delete("typescript_test");
    } catch (e) {
      // Ignore if collection doesn't exist
    }

    const collection = await client.collections.create("typescript_test", [
      { name: "title", type: "string" },
      { name: "content", type: "string", vectorize: false }, // No vectorize to avoid embedding provider requirement
    ]);
    console.log("   ✅ Collection created:", collection.name);

    // Create a record
    console.log("\n4. Creating record...");
    const record = await client.records.create("typescript_test", {
      title: "Hello from TypeScript",
      content: "This is a test record created using the TypeScript SDK!",
    });
    console.log("   ✅ Record created:", record.id);
    console.log("   Data:", record.data);

    // List records
    console.log("\n5. Listing records...");
    const records = await client.records.list("typescript_test");
    console.log(`   ✅ Found ${records.total} records`);

    // Note: Search requires vectorize=True, so we skip it for this basic example
    console.log("\n6. Skipping search (requires vectorize=True)...");
    console.log("   ℹ️  To test search, create a collection with vectorize enabled and embedding_provider");

    // Cleanup
    console.log("\n7. Cleaning up...");
    await client.collections.delete("typescript_test");
    console.log("   ✅ Collection deleted");

    console.log("\n✅ Example completed successfully!");
  } catch (error) {
    console.error("❌ Error:", error);
  }

  await client.close();
}

main();
