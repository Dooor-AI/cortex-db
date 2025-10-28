'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function LoginPage() {
  const router = useRouter();
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Verify the API key by making a test request
      const res = await fetch('http://localhost:8000/api-keys', {
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
      });

      if (res.ok) {
        // Key is valid and has admin access
        localStorage.setItem('cortexdb_api_key', apiKey);
        router.push('/');
      } else if (res.status === 401) {
        setError('Invalid API key');
      } else if (res.status === 403) {
        setError('This API key does not have admin access');
      } else {
        setError('Failed to verify API key');
      }
    } catch (err) {
      setError('Failed to connect to CortexDB. Is the gateway running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-950 px-4 text-neutral-200">
      <Card className="w-full max-w-md p-8 bg-neutral-900 border border-neutral-800">
        <div className="mb-8">
          <h1 className="text-xl font-semibold tracking-wide font-mono text-neutral-100">
            cortexdb // login
          </h1>
          <p className="text-sm text-neutral-400 mt-2 font-mono">
            enter admin api key to continue
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <Label htmlFor="apiKey" className="text-neutral-300 font-mono">admin api key</Label>
            <Input
              id="apiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="cortexdb_admin_..."
              className="mt-1 font-mono bg-neutral-950 border-neutral-800 text-neutral-100 placeholder:text-neutral-600 focus-visible:ring-neutral-600"
              autoFocus
            />
            <p className="text-xs text-neutral-500 mt-1 font-mono">
              shown once on first gateway start; can be rotated later
            </p>
          </div>

          {error && (
            <div className="p-3 bg-neutral-950 border border-red-900/60 rounded-md">
              <p className="text-sm text-red-400 font-mono">{error}</p>
            </div>
          )}

          <Button
            type="submit"
            className="w-full bg-neutral-800 hover:bg-neutral-700 text-neutral-100 border border-neutral-700 font-mono"
            disabled={!apiKey || loading}
          >
            {loading ? 'verifying…' : 'login'}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <details className="text-sm text-neutral-500">
            <summary className="cursor-pointer hover:text-neutral-300 transition-colors font-mono">
              where do i find my api key?
            </summary>
            <div className="mt-4 text-left bg-neutral-950 p-4 rounded-md space-y-2 border border-neutral-800">
              <p className="font-mono text-neutral-400">displayed at first gateway startup:</p>
              <pre className="bg-neutral-900 p-3 rounded border border-neutral-800 text-xs overflow-x-auto text-neutral-200 font-mono">
{`CORTEXDB ADMIN API KEY CREATED
API Key: cortexdb_admin_abc123...`}
              </pre>
              <p className="text-[11px] text-neutral-500 font-mono">
                lost it? set CORTEXDB_ADMIN_KEY in your .env and restart the gateway
              </p>
            </div>
          </details>
        </div>
      </Card>
    </div>
  );
}

