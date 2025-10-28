"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  createEmbeddingProvider,
  deleteEmbeddingProvider,
  EmbeddingProviderCreateRequest,
  EmbeddingProviderSummary,
  fetchEmbeddingProviders,
} from "@/lib/cortex-client";
import { APIKeysSection } from "@/components/api-keys-section";

const DEFAULT_MODEL = "models/text-embedding-004";

export default function EmbeddingSettingsPage() {
  const [providers, setProviders] = useState<EmbeddingProviderSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [form, setForm] = useState<EmbeddingProviderCreateRequest>({
    name: "",
    provider: "gemini",
    embedding_model: DEFAULT_MODEL,
    api_key: "",
    metadata: {},
  });

  useEffect(() => {
    void loadProviders();
  }, []);

  const sortedProviders = useMemo(() => {
    return [...providers].sort((a, b) => a.name.localeCompare(b.name));
  }, [providers]);

  async function loadProviders() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchEmbeddingProviders();
      setProviders(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load providers");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (!form.name.trim()) {
      setError("Please provide a name to identify the provider.");
      return;
    }
    if (!form.api_key.trim()) {
      setError("Please include the API key before saving.");
      return;
    }

    try {
      setSubmitting(true);
      const payload: EmbeddingProviderCreateRequest = {
        ...form,
        name: form.name.trim(),
        embedding_model: form.embedding_model.trim() || DEFAULT_MODEL,
        api_key: form.api_key.trim(),
      };
      const created = await createEmbeddingProvider(payload);
      setProviders((prev) => [...prev, created]);
      setSuccess(`Provider "${created.name}" configured successfully.`);
      setForm({
        name: "",
        provider: "gemini",
        embedding_model: DEFAULT_MODEL,
        api_key: "",
        metadata: {},
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error saving provider");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    const provider = providers.find((item) => item.id === id);
    if (!provider) return;
    const confirmed = window.confirm(
      `Remove provider "${provider.name}"? Collections using it will fall back to the default configuration.`,
    );
    if (!confirmed) return;

    try {
      setDeletingId(id);
      await deleteEmbeddingProvider(id);
      setProviders((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error removing provider");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="container space-y-8 py-10">
      <div className="space-y-1">
        <h1 className="text-3xl font-semibold text-primary">Configuration</h1>
        <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
          Manage API keys and embedding providers for CortexDB.
        </p>
      </div>

      <div className="space-y-8">
        <div className="space-y-1">
          <h2 className="text-2xl font-semibold text-primary">Tokens</h2>
          <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
            Manage API tokens for authentication and authorization.
          </p>
        </div>
        
        <APIKeysSection />
        
        <div className="space-y-1">
          <h2 className="text-2xl font-semibold text-primary">Embedding Providers</h2>
          <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
            Manage credentials and models available for vectorization.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Add Provider</CardTitle>
            <CardDescription>Save API keys to enable dedicated embeddings.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4" onSubmit={handleCreate}>
              <div className="grid gap-2">
                <label className="text-sm font-medium text-muted-foreground">Internal name</label>
                <Input
                  value={form.name}
                  onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                  placeholder="prod-gemini"
                  required
                />
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium text-muted-foreground">Provider</label>
                <select
                  className="h-10 rounded-md border border-border/70 bg-background px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary"
                  value={form.provider}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, provider: event.target.value as "gemini" }))
                  }
                >
                  <option value="gemini">Gemini (Google)</option>
                </select>
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium text-muted-foreground">Embedding model</label>
                <Input
                  value={form.embedding_model}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, embedding_model: event.target.value }))
                  }
                  placeholder={DEFAULT_MODEL}
                />
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium text-muted-foreground">API key</label>
                <Input
                  type="password"
                  value={form.api_key}
                  onChange={(event) => setForm((prev) => ({ ...prev, api_key: event.target.value }))}
                  placeholder="AIza..."
                  required
                />
                <p className="text-xs text-muted-foreground">
                  We store the key only on the backend. It is never exposed to the frontend.
                </p>
              </div>

              {error ? (
                <p className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </p>
              ) : null}
              {success ? (
                <p className="rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-500">
                  {success}
                </p>
              ) : null}

              <div className="flex justify-end">
                <Button type="submit" disabled={submitting} className="min-w-[160px]">
                  {submitting ? "Saving…" : "Save provider"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card className="h-full">
          <CardHeader>
            <CardTitle>Configured Providers</CardTitle>
            <CardDescription>
              Define multiple providers and choose which one to use for each collection.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : sortedProviders.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No providers configured. You must add at least one provider to enable embeddings.
              </p>
            ) : (
              <div className="space-y-3">
                {sortedProviders.map((provider) => (
                  <div
                    key={provider.id}
                    className="flex flex-col gap-3 rounded-lg border border-border/70 bg-secondary/20 p-4 md:flex-row md:items-center md:justify-between"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-primary">{provider.name}</span>
                        <Badge variant="outline">{provider.provider}</Badge>
                        <Badge variant={provider.enabled ? "secondary" : "outline"}>
                          {provider.enabled ? "active" : "inactive"}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Model: {provider.embedding_model}
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      className="text-destructive hover:text-destructive"
                      disabled={deletingId === provider.id}
                      onClick={() => void handleDelete(provider.id)}
                    >
                      {deletingId === provider.id ? "Removing…" : "Remove"}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
        </div>
      </div>
    </div>
  );
}
