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
      setError(err instanceof Error ? err.message : "Falha ao carregar provedores");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (!form.name.trim()) {
      setError("Informe um nome para identificar o provedor.");
      return;
    }
    if (!form.api_key.trim()) {
      setError("Inclua a API key antes de salvar.");
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
      setSuccess(`Provedor "${created.name}" configurado com sucesso.`);
      setForm({
        name: "",
        provider: "gemini",
        embedding_model: DEFAULT_MODEL,
        api_key: "",
        metadata: {},
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar provedor");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    const provider = providers.find((item) => item.id === id);
    if (!provider) return;
    const confirmed = window.confirm(
      `Remover o provedor "${provider.name}"? Coleções que o usam voltarão a usar a configuração padrão.`,
    );
    if (!confirmed) return;

    try {
      setDeletingId(id);
      await deleteEmbeddingProvider(id);
      setProviders((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao remover provedor");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="container space-y-8 py-10">
      <div className="space-y-1">
        <h1 className="text-3xl font-semibold text-primary">Embedding Providers</h1>
        <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
          Gerencie credenciais e modelos disponíveis para vetorização.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Adicionar provedor</CardTitle>
            <CardDescription>Salve chaves de API para habilitar embeddings dedicados.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4" onSubmit={handleCreate}>
              <div className="grid gap-2">
                <label className="text-sm font-medium text-muted-foreground">Nome interno</label>
                <Input
                  value={form.name}
                  onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                  placeholder="prod-gemini"
                  required
                />
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium text-muted-foreground">Provedor</label>
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
                  Armazenamos a chave somente no backend. Ela nunca é publicada para o frontend.
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
                  {submitting ? "Salvando…" : "Salvar provedor"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card className="h-full">
          <CardHeader>
            <CardTitle>Provedores configurados</CardTitle>
            <CardDescription>
              Defina múltiplos provedores e escolha em cada coleção qual usar.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <p className="text-sm text-muted-foreground">Carregando…</p>
            ) : sortedProviders.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Nenhum provedor salvo. As coleções usarão a variável de ambiente global GEMINI_API_KEY.
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
                          {provider.enabled ? "ativo" : "inativo"}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Modelo: {provider.embedding_model}
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      className="text-destructive hover:text-destructive"
                      disabled={deletingId === provider.id}
                      onClick={() => void handleDelete(provider.id)}
                    >
                      {deletingId === provider.id ? "Removendo…" : "Remover"}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
