import Link from "next/link";
import { notFound } from "next/navigation";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchCollectionSchema, fetchRecordDetail } from "@/lib/cortex-client";
import { formatDate } from "@/lib/format";
import { Button } from "@/components/ui/button";
import { SchemaField } from "@/lib/types";
import { FilePreview } from "@/components/file-preview";
import { VectorChunks } from "@/components/vector-chunks";
import { CollapsibleSection } from "@/components/collapsible-section";
import { RecordFields } from "@/components/record-fields";

interface PageProps {
  params: Promise<{ database: string; name: string; id: string }>;
}

export default async function RecordDetailPage({ params }: PageProps) {
  const { database, name, id } = await params;

  const [schema, payload] = await Promise.all([
    fetchCollectionSchema(name).catch(() => null),
    fetchRecordDetail(name, id).catch(() => null),
  ]);

  if (!schema || !payload) {
    notFound();
  }

  const record = payload.record ?? payload;
  const files: Record<string, string> = payload.files ?? {};
  const schemaFields: SchemaField[] = (schema.fields as SchemaField[] | undefined) ?? [];

  return (
    <div className="container space-y-8 py-10">
      <nav className="flex items-center gap-2 text-[0.7rem] uppercase tracking-[0.35em] text-muted-foreground">
        <Link href={`/databases/${database}/collections`} className="hover:text-primary">
          {database}
        </Link>
        <span>/</span>
        <Link href={`/databases/${database}/collections/${name}`} className="hover:text-primary">
          {name}
        </Link>
        <span>/</span>
        <span className="text-primary">{id}</span>
      </nav>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="space-y-4">
          {/* Record Fields */}
          <CollapsibleSection
            heading="Record Fields"
            title="Structured Data"
            description="Field values as defined in the collection schema."
            defaultOpen={true}
          >
            <RecordFields record={record} schemaFields={schemaFields} files={files} />
          </CollapsibleSection>

          {/* File Previews */}
          {Object.keys(files).length > 0 && (
            <CollapsibleSection
              heading="File Previews"
              title="Attached Files"
              description={`${Object.keys(files).length} file${Object.keys(files).length !== 1 ? "s" : ""} attached to this record.`}
              defaultOpen={false}
            >
              <div className="space-y-6">
                {Object.entries(files).map(([fieldName, _url]) => {
                  const filePath = record[fieldName] as string;
                  return (
                    <FilePreview
                      key={fieldName}
                      fieldName={fieldName}
                      filePath={filePath}
                      collectionName={name}
                      recordId={id}
                    />
                  );
                })}
              </div>
            </CollapsibleSection>
          )}

          {/* Vector Chunks */}
          {schemaFields.some((field) => field.vectorize) && (
            <CollapsibleSection
              heading="Vectorized Chunks"
              title="Text Embeddings"
              description="Text chunks extracted and vectorized for semantic search."
              defaultOpen={false}
            >
              <VectorChunks collectionName={name} recordId={id} />
            </CollapsibleSection>
          )}

          {/* Record Payload */}
          <CollapsibleSection
            heading="Raw JSON Payload"
            title={`ID / ${id}`}
            description="Raw document view as received from CortexDB gateway."
            defaultOpen={false}
          >
            <pre className="max-h-[70vh] overflow-auto rounded-md border border-border/60 bg-secondary/40 p-4 text-xs text-primary">
              {JSON.stringify(record, null, 2)}
            </pre>
          </CollapsibleSection>
        </div>

        <aside className="space-y-4">
          <Card>
            <CardHeader>
              <div className="terminal-heading">Meta</div>
              <CardTitle className="text-primary">Record Signals</CardTitle>
              <CardDescription>Context derived from payload headers.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-muted-foreground">
              <div className="flex items-center justify-between">
                <span className="terminal-heading text-muted-foreground/70">Created</span>
                <span className="font-mono text-[0.75rem] text-primary">
                  {formatDate((record.created_at as string) ?? payload.record?.created_at)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="terminal-heading text-muted-foreground/70">Updated</span>
                <span className="font-mono text-[0.75rem] text-primary">
                  {formatDate((record.updated_at as string) ?? payload.record?.updated_at)}
                </span>
              </div>
              <div className="terminal-divider" />
              <div className="space-y-2">
                <span className="terminal-heading">Files Linked</span>
                {Object.keys(files).length === 0 ? (
                  <p className="text-[0.7rem]">No files associated.</p>
                ) : (
                  <ul className="space-y-2 text-[0.7rem]">
                    {Object.entries(files).map(([field, url]) => (
                      <li key={field} className="flex items-center justify-between gap-2">
                        <span className="font-mono text-primary">{field}</span>
                        <Button asChild size="sm" variant="outline">
                          <a href={url} target="_blank" rel="noopener noreferrer">
                            Download
                          </a>
                        </Button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="terminal-heading">Vector Fields</div>
              <CardTitle className="text-primary">Embedding Targets</CardTitle>
              <CardDescription>Fields configured for automatic vectorization.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {schemaFields.filter((field) => field.vectorize).map((field) => (
                <Badge key={field.name} variant="outline">
                  {field.name}
                </Badge>
              ))}
              {schemaFields.filter((field) => field.vectorize).length === 0 ? (
                <p className="text-[0.7rem] text-muted-foreground">None configured.</p>
              ) : null}
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}
