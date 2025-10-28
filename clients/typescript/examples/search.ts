/** CortexDB Semantic Search Example */

import { CortexClient, FieldType } from "../src";

async function main() {
  console.log("=== CortexDB Semantic Search Example ===\n");

  const client = new CortexClient({
    baseUrl: "http://localhost:8000",
  });

  try {
    // Note: This example requires:
    // 1. An embedding provider configured in CortexDB
    // 2. Pass the provider ID when creating the collection

    const EMBEDDING_PROVIDER_ID = process.env.EMBEDDING_PROVIDER_ID;
    if (!EMBEDDING_PROVIDER_ID) {
      console.log("⚠️  EMBEDDING_PROVIDER_ID not set");
      console.log("   Set it with: export EMBEDDING_PROVIDER_ID=your-provider-id");
      console.log("   Skipping semantic search example...\n");
      return;
    }

    // Clean up if exists
    try {
      await client.collections.delete("knowledge_base");
    } catch (e) {
      // Ignore
    }

    // Create collection with vectorization enabled
    console.log("1. Creating Collection with Vectorization");
    await client.collections.create(
      "knowledge_base",
      [
        { name: "title", type: "string" as FieldType },
        { name: "content", type: "string" as FieldType, vectorize: true },
        { name: "category", type: "string" as FieldType },
      ],
      EMBEDDING_PROVIDER_ID // Required for vectorization
    );
    console.log("   ✓ Collection created\n");

    // Add knowledge base entries
    console.log("2. Adding Knowledge Base Entries");
    const entries = [
      {
        title: "Python Programming",
        content:
          "Python is a high-level, interpreted programming language known for its simplicity and readability.",
        category: "programming",
      },
      {
        title: "Machine Learning",
        content:
          "Machine learning is a branch of artificial intelligence that focuses on building systems that learn from data.",
        category: "ai",
      },
      {
        title: "Web Development",
        content:
          "Web development involves creating websites and web applications using technologies like HTML, CSS, and JavaScript.",
        category: "programming",
      },
      {
        title: "Deep Learning",
        content:
          "Deep learning uses neural networks with multiple layers to model complex patterns in data.",
        category: "ai",
      },
    ];

    for (const entry of entries) {
      await client.records.create("knowledge_base", entry);
      console.log(`   ✓ Added: ${entry.title}`);
    }
    console.log();

    // Perform semantic search
    console.log("3. Semantic Search");
    console.log('   Query: "How do I learn AI?"\n');

    const results = await client.records.search(
      "knowledge_base",
      "How do I learn AI?",
      undefined,
      3
    );

    console.log(`   Found ${results.total} results (took ${results.took_ms}ms):\n`);

    results.results.forEach((result, idx) => {
      console.log(`   ${idx + 1}. ${result.record.data.title}`);
      console.log(`      Score: ${result.score.toFixed(4)}`);
      console.log(`      Category: ${result.record.data.category}`);
      console.log(`      Content: ${result.record.data.content.substring(0, 80)}...`);
      console.log();
    });

    // Search with filters
    console.log("4. Semantic Search with Filters");
    console.log('   Query: "coding languages"');
    console.log('   Filter: category = "programming"\n');

    const filteredResults = await client.records.search(
      "knowledge_base",
      "coding languages",
      { category: "programming" },
      2
    );

    console.log(
      `   Found ${filteredResults.total} results (took ${filteredResults.took_ms}ms):\n`
    );

    filteredResults.results.forEach((result, idx) => {
      console.log(`   ${idx + 1}. ${result.record.data.title}`);
      console.log(`      Score: ${result.score.toFixed(4)}`);
      console.log();
    });

    // Cleanup
    console.log("5. Cleanup");
    await client.collections.delete("knowledge_base");
    console.log("   ✓ Collection deleted\n");

    console.log("✅ Search example completed successfully!");
  } catch (error) {
    console.error("❌ Error:", error);
    throw error;
  } finally {
    await client.close();
  }
}

main().catch(console.error);

