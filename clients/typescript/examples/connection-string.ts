/** Example: Using Connection Strings */

import { CortexClient } from '../src';

async function main() {
  console.log('=== CortexDB Connection String Examples ===\n');

  // Example 1: Simple localhost
  console.log('1. Simple localhost connection:');
  const client1 = new CortexClient('cortexdb://localhost:8000');
  console.log('   ✓ Connected to http://localhost:8000\n');

  // Example 2: With API key
  console.log('2. Connection with API key:');
  const client2 = new CortexClient('cortexdb://my_api_key_123@localhost:8000');
  console.log('   ✓ Connected with API key: my_api_key_123\n');

  // Example 3: Production HTTPS (auto-detected)
  console.log('3. Production connection (HTTPS auto-detected):');
  const client3 = new CortexClient('cortexdb://prod_key@api.cortexdb.com');
  console.log('   ✓ Connected to https://api.cortexdb.com\n');

  // Example 4: Explicit HTTPS port
  console.log('4. Explicit HTTPS port 443:');
  const client4 = new CortexClient('cortexdb://key@api.cortexdb.com:443');
  console.log('   ✓ Connected to https://api.cortexdb.com:443\n');

  // Example 5: Custom port
  console.log('5. Custom port:');
  const client5 = new CortexClient('cortexdb://localhost:3000');
  console.log('   ✓ Connected to http://localhost:3000\n');

  // Example 6: Compare with traditional way
  console.log('6. Traditional way (still works):');
  const client6 = new CortexClient({
    baseUrl: 'http://localhost:8000',
    apiKey: 'my_key'
  });
  console.log('   ✓ Connected using options object\n');

  // Test actual connection
  console.log('7. Testing connection health:');
  try {
    const health = await client1.health();
    console.log(`   ✓ Gateway is ${health.status}\n`);
  } catch (error) {
    console.log('   ⚠️  Gateway not running (expected in CI)\n');
  }

  console.log('=== Connection String Format ===');
  console.log('cortexdb://[api_key@]host[:port]');
  console.log('');
  console.log('Benefits:');
  console.log('  • Single string configuration');
  console.log('  • Easy to store in environment variables');
  console.log('  • Familiar pattern (like PostgreSQL, MongoDB, Redis)');
  console.log('  • Auto-detects HTTP vs HTTPS');

  await client1.close();
}

main().catch(console.error);

