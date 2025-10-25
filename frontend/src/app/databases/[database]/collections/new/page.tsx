"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useParams } from "next/navigation";

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
import { Textarea } from "@/components/ui/textarea";
import {
  CollectionSchema,
  EmbeddingProviderSummary,
  apiRequest,
  fetchEmbeddingProviders,
} from "@/lib/cortex-client";

type StoreLocation = "postgres" | "qdrant" | "qdrant_payload" | "minio";
type FieldType =
  | "string"
  | "text"
  | "int"
  | "float"
  | "boolean"
  | "date"
  | "datetime"
  | "enum"
  | "array"
  | "file"
  | "json";

type FieldState = {
  id: string;
  name: string;
  type: FieldType;
  required: boolean;
  indexed: boolean;
  unique: boolean;
  filterable: boolean;
  vectorize: boolean;
  store_in: StoreLocation[];
  enum_values: string;
  extract_text: boolean;
  ocr_if_needed: boolean;
};

const FIELD_OPTIONS: Array<{ value: FieldType; label: string }> = [
  { value: "string", label: "String" },
  { value: "text", label: "Long Text" },
  { value: "int", label: "Integer" },
  { value: "float", label: "Float" },
  { value: "boolean", label: "Boolean" },
  { value: "date", label: "Date" },
  { value: "datetime", label: "DateTime" },
  { value: "enum", label: "Enum" },
  { value: "json", label: "JSON" },
  { value: "file", label: "File" },
  { value: "array", label: "Array (advanced)" },
];

const STORE_OPTIONS: Array<{ value: StoreLocation; label: string; hint?: string }> = [
  { value: "postgres", label: "Postgres", hint: "Structured fields & references" },
  { value: "qdrant", label: "Qdrant", hint: "Vector index" },
  { value: "qdrant_payload", label: "Qdrant Payload", hint: "Metadata on vectors" },
  { value: "minio", label: "MinIO", hint: "Binary/file storage" },
];

const DEFAULT_EMBEDDING_MODEL = "models/text-embedding-004";

function randomId() {
  return Math.random().toString(36).slice(2);
}

function createDefaultField(): FieldState {
  return {
    id: randomId(),
    name: "",
    type: "string",
    required: false,
    indexed: false,
    unique: false,
    filterable: false,
    vectorize: false,
    store_in: ["postgres"],
    enum_values: "",
    extract_text: true,
    ocr_if_needed: true,
  };
}

export default function CreateCollectionPage() {
  const router = useRouter();
  const params = useParams();
  const database = params.database as string;

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [embeddingModel, setEmbeddingModel] = useState(DEFAULT_EMBEDDING_MODEL);
  const [providers, setProviders] = useState<EmbeddingProviderSummary[]>([]);
  const [providerId, setProviderId] = useState("");
  const [providersLoading, setProvidersLoading] = useState(true);
  const [chunkSize, setChunkSize] = useState("");
  const [chunkOverlap, setChunkOverlap] = useState("");
  const [fields, setFields] = useState<FieldState[]>([createDefaultField()]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const vectorEligibleTypes: FieldType[] = useMemo(() => ["string", "text", "file"], []);
  const availableProviders = useMemo(
    () => providers.filter((provider) => provider.enabled),
    [providers],
  );

  useEffect(() => {
    let active = true;

    (async () => {
      try {
        const result = await fetchEmbeddingProviders();
        if (active) {
          setProviders(result);
        }
      } catch (err) {
        if (active && process.env.NODE_ENV !== "production") {
          console.warn("Failed to load embedding providers", err);
        }
        if (active) {
          setProviders([]);
        }
      } finally {
        if (active) {
          setProvidersLoading(false);
        }
      }
    })();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!providerId) {
      return;
    }
    const provider = providers.find((item) => item.id === providerId);
    if (provider) {
      setEmbeddingModel(provider.embedding_model);
    }
  }, [providerId, providers]);

  function updateField(id: string, patch: Partial<FieldState>) {
    setFields((prev) =>
      prev.map((field) => {
        if (field.id !== id) return field;
        const next: FieldState = { ...field, ...patch };
        if (!vectorEligibleTypes.includes(next.type)) {
          next.vectorize = false;
        }
        if (next.type === "file") {
          next.store_in = Array.from(
            new Set([...next.store_in, "minio", "qdrant_payload", "postgres"])
          ) as StoreLocation[];
          next.extract_text = true;
          next.ocr_if_needed = true;
        }
        if (field.type === "file" && next.type !== "file") {
          next.extract_text = true;
          next.ocr_if_needed = true;
          next.store_in = next.store_in.filter((item) => item !== "minio");
        }
        if (next.type !== "enum") {
          next.enum_values = "";
        }
        return next;
      })
    );
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (!name.trim()) {
      setError("Collection name is required.");
      return;
    }

    if (fields.length === 0) {
      setError("Add at least one field to the schema.");
      return;
    }

    for (const field of fields) {
      if (!field.name.trim()) {
        setError("Every field must have a name.");
        return;
      }
      if (!field.store_in.length) {
        setError(`Field "${field.name || "unnamed"}" needs at least one storage target.`);
        return;
      }
      if (field.type === "enum" && !field.enum_values.trim()) {
        setError(`Enum field "${field.name}" needs at least one value.`);
        return;
      }
      if (field.type === "array") {
        setError("Array fields are not supported in the visual builder yet.");
        return;
      }
    }

    const schemaPayload: CollectionSchema = {
      name: name.trim(),
      description: description.trim() || undefined,
      fields: fields.map((field) => {
        const base = {
          name: field.name.trim(),
          type: field.type,
          required: field.required || undefined,
          indexed: field.indexed || undefined,
          unique: field.unique || undefined,
          filterable: field.filterable || undefined,
          vectorize: field.vectorize || undefined,
          store_in: field.store_in,
        } as any;

        if (field.type === "enum") {
          base.values = field.enum_values
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean);
        }

        if (field.type === "file") {
          base.extract_config = {
            extract_text: field.extract_text,
            ocr_if_needed: field.ocr_if_needed,
          };
        }

        if (base.vectorize && !base.store_in.includes("qdrant")) {
          base.store_in = Array.from(new Set([...base.store_in, "qdrant"]));
        }

        if (!base.vectorize) {
          delete base.vectorize;
        }

        return base;
      }),
    };

    const config: Record<string, unknown> = {};
    const trimmedModel = embeddingModel.trim();
    if (trimmedModel) config.embedding_model = trimmedModel;
    if (providerId) config.embedding_provider_id = providerId;
    if (chunkSize.trim()) config.chunk_size = Number(chunkSize);
    if (chunkOverlap.trim()) config.chunk_overlap = Number(chunkOverlap);
    if (Object.keys(config).length) {
      schemaPayload.config = config;
    }

    try {
      setIsSubmitting(true);
      const res = await apiRequest(`/databases/${encodeURIComponent(database)}/collections`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(schemaPayload),
      });
      const response = await res.json();
      setSuccess(`Collection "${response.collection}" created successfully in database "${database}".`);
      setTimeout(() => {
        router.refresh(); // Force refresh to clear cache
        router.push(`/databases/${encodeURIComponent(database)}/collections`);
      }, 1200);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to create collection.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="container space-y-8 py-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-primary">
            {database} / New Collection
          </h1>
          <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
            Compose schema, vector routing, and storage in one step.
          </p>
        </div>
        <Button variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Collection Details</CardTitle>
            <CardDescription>Identify how this dataset should be tracked.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid gap-2">
              <label className="text-sm font-medium text-muted-foreground">Name</label>
              <Input
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="support_tickets"
                required
              />
            </div>
            <div className="grid gap-2">
              <label className="text-sm font-medium text-muted-foreground">Description</label>
              <Textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="What this collection stores..."
                rows={3}
              />
            </div>
            <div className="grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
              <div className="grid gap-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-muted-foreground">Embedding provider</label>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => router.push("/settings/embeddings")}
                  >
                    Manage
                  </Button>
                </div>
                <select
                  className="h-10 rounded-md border border-border/70 bg-background px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
                  value={providerId}
                  onChange={(event) => setProviderId(event.target.value)}
                  disabled={providersLoading}
                  required
                >
                  <option value="">
                    {providersLoading ? "Loading providers…" : "Select a provider"}
                  </option>
                  {availableProviders.map((provider) => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name} · {provider.provider}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-muted-foreground">
                  {providersLoading
                    ? "Fetching configured providers…"
                    : availableProviders.length === 0
                      ? "No providers configured. Please add one in settings before creating collections with vectorization."
                      : "Select which provider should supply embeddings for this collection."}
                </p>
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium text-muted-foreground">Embedding model</label>
                <Input
                  value={embeddingModel}
                  onChange={(event) => setEmbeddingModel(event.target.value)}
                  placeholder="models/text-embedding-004"
                  disabled
                />
                <p className="text-xs text-muted-foreground">
                  Automatically set by the selected provider.
                </p>
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="grid gap-2">
                <label className="text-sm font-medium text-muted-foreground">Chunk size</label>
                <Input
                  value={chunkSize}
                  onChange={(event) => setChunkSize(event.target.value)}
                  type="number"
                  min="0"
                  placeholder="1024"
                />
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-medium text-muted-foreground">Chunk overlap</label>
                <Input
                  value={chunkOverlap}
                  onChange={(event) => setChunkOverlap(event.target.value)}
                  type="number"
                  min="0"
                  placeholder="128"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Fields</CardTitle>
            <CardDescription>
              Define how data maps into Postgres, Qdrant, and MinIO. Vector fields will be embedded automatically.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {fields.map((field, index) => {
              const isFile = field.type === "file";
              const isEnum = field.type === "enum";
              const vectorDisabled = !vectorEligibleTypes.includes(field.type);
              return (
                <div key={field.id} className="rounded-lg border border-border/70 bg-secondary/20 p-4 space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <Badge variant="outline">Field {index + 1}</Badge>
                    {fields.length > 1 ? (
                      <Button
                        type="button"
                        variant="ghost"
                        className="text-xs text-destructive hover:text-destructive"
                        onClick={() => setFields((prev) => prev.filter((item) => item.id !== field.id))}
                      >
                        Remove
                      </Button>
                    ) : null}
                  </div>
                  <div className="grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
                    <div className="grid gap-3">
                      <div className="grid gap-2">
                        <label className="text-sm font-medium text-muted-foreground">Name</label>
                        <Input
                          value={field.name}
                          onChange={(event) => updateField(field.id, { name: event.target.value })}
                          placeholder="subject"
                          required
                        />
                      </div>
                    </div>
                    <div className="grid gap-2">
                      <label className="text-sm font-medium text-muted-foreground">Type</label>
                      <select
                        className="h-10 rounded-md border border-border/70 bg-background px-3 text-sm text-foreground"
                        value={field.type}
                        onChange={(event) =>
                          updateField(field.id, { type: event.target.value as FieldType })
                        }
                      >
                        {FIELD_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      {field.type === "array" ? (
                        <p className="text-[0.7rem] text-muted-foreground">
                          Nested schemas are coming soon. Use the API if you need arrays now.
                        </p>
                      ) : null}
                    </div>
                  </div>
                  {isEnum ? (
                    <div className="grid gap-2">
                      <label className="text-sm font-medium text-muted-foreground">Enum values</label>
                      <Input
                        value={field.enum_values}
                        onChange={(event) =>
                          updateField(field.id, { enum_values: event.target.value })
                        }
                        placeholder="comma,separated,values"
                      />
                    </div>
                  ) : null}
                  <div className="grid gap-3 md:grid-cols-2">
                    <ToggleRow
                      label="Required"
                      checked={field.required}
                      onChange={(value) => updateField(field.id, { required: value })}
                    />
                    <ToggleRow
                      label="Indexed"
                      checked={field.indexed}
                      onChange={(value) => updateField(field.id, { indexed: value })}
                    />
                    <ToggleRow
                      label="Unique"
                      checked={field.unique}
                      onChange={(value) => updateField(field.id, { unique: value })}
                    />
                    <ToggleRow
                      label="Filterable"
                      checked={field.filterable}
                      onChange={(value) => updateField(field.id, { filterable: value })}
                    />
                    <ToggleRow
                      label="Vectorize"
                      checked={field.vectorize}
                      disabled={vectorDisabled}
                      hint={vectorDisabled ? "Only available for string, text, or file." : undefined}
                      onChange={(value) => updateField(field.id, { vectorize: value })}
                    />
                  </div>
                  <div className="space-y-3">
                    <p className="text-sm font-medium text-muted-foreground">Store in</p>
                    <div className="grid gap-2 md:grid-cols-2">
                      {STORE_OPTIONS.map((option) => (
                        <label
                          key={option.value}
                          className="flex cursor-pointer items-start gap-2 rounded-md border border-border/70 bg-background/70 px-3 py-2 text-sm"
                        >
                          <input
                            type="checkbox"
                            className="mt-1"
                            checked={field.store_in.includes(option.value)}
                            onChange={(event) => {
                              const checked = event.target.checked;
                              updateField(field.id, {
                                store_in: checked
                                  ? Array.from(new Set([...field.store_in, option.value])) as StoreLocation[]
                                  : field.store_in.filter((value) => value !== option.value),
                              });
                            }}
                          />
                          <span>
                            {option.label}
                            {option.hint ? (
                              <span className="block text-xs text-muted-foreground">{option.hint}</span>
                            ) : null}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                  {isFile ? (
                    <div className="grid gap-3 md:grid-cols-2">
                      <ToggleRow
                        label="Extract text"
                        checked={field.extract_text}
                        onChange={(value) => updateField(field.id, { extract_text: value })}
                      />
                      <ToggleRow
                        label="OCR if needed"
                        checked={field.ocr_if_needed}
                        onChange={(value) => updateField(field.id, { ocr_if_needed: value })}
                      />
                    </div>
                  ) : null}
                </div>
              );
            })}
            <Button
              type="button"
              variant="secondary"
              onClick={() => setFields((prev) => [...prev, createDefaultField()])}
            >
              Add field
            </Button>
          </CardContent>
        </Card>

        {error ? (
          <Card className="border-destructive/60 bg-destructive/10">
            <CardContent className="py-4 text-sm text-destructive">{error}</CardContent>
          </Card>
        ) : null}
        {success ? (
          <Card className="border-emerald-600/60 bg-emerald-600/10">
            <CardContent className="py-4 text-sm text-emerald-500">{success}</CardContent>
          </Card>
        ) : null}

        <div className="flex items-center justify-end gap-3">
          <Button
            type="submit"
            disabled={isSubmitting}
            className="min-w-[160px]"
          >
            {isSubmitting ? "Creating..." : "Create collection"}
          </Button>
        </div>
      </form>
    </div>
  );
}

type ToggleRowProps = {
  label: string;
  checked: boolean;
  disabled?: boolean;
  hint?: string;
  onChange: (value: boolean) => void;
};

function ToggleRow({ label, checked, disabled, hint, onChange }: ToggleRowProps) {
  return (
    <label className="flex cursor-pointer items-center justify-between rounded-md border border-border/70 bg-background/70 px-3 py-2 text-sm">
      <span className="flex flex-col">
        {label}
        {hint ? <span className="text-xs text-muted-foreground">{hint}</span> : null}
      </span>
      <input
        type="checkbox"
        className="h-4 w-4"
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
      />
    </label>
  );
}
