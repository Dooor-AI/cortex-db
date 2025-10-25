import Link from "next/link";
import { notFound } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RecordsToolbar } from "@/components/records-toolbar";
import { PaginationControls } from "@/components/pagination-controls";
import { RecordsTable, RecordRow, FieldSummary } from "@/components/records-table";
import { AddRecordDialog } from "@/components/add-record-dialog";
import { FiltersWrapper } from "@/components/filters-wrapper";
import {
  fetchCollectionRecords,
  fetchCollectionSchema,
  searchCollection,
} from "@/lib/cortex-client";
import { SchemaField } from "@/lib/types";

interface PageProps {
  params: Promise<{ database: string; name: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function CollectionDetailPage({ params, searchParams }: PageProps) {
  const { database, name } = await params;
  const search = await searchParams;

  const limit = Math.min(
    100,
    Math.max(1, Number(typeof search.limit === "string" ? search.limit : search.limit?.[0] ?? 20))
  );
  const page = Math.max(1, Number(typeof search.page === "string" ? search.page : search.page?.[0] ?? 1));
  const query = typeof search.q === "string" ? search.q : search.q?.[0] ?? "";

  // Parse filters from URL (JSON encoded)
  let filters: Record<string, any> = {};
  const filtersParam = typeof search.filters === "string" ? search.filters : search.filters?.[0];
  if (filtersParam) {
    try {
      filters = JSON.parse(filtersParam);
    } catch {
      // Invalid JSON, ignore
    }
  }

  const schema = await fetchCollectionSchema(name).catch(() => null);
  if (!schema) {
    notFound();
  }

  const schemaFields = (schema.fields as SchemaField[] | undefined) ?? [];
  const viewFields: FieldSummary[] = schemaFields
    .filter((field) => field.type !== "array" && field.type !== "file")
    .map((field) => ({ name: field.name, type: field.type }));

  const offset = (page - 1) * limit;

  let records: RecordRow[] = [];
  let total = 0;
  const searchMode = Boolean(query);
  const filterMode = Object.keys(filters).length > 0;
  let took: number | undefined;

  if (query) {
    const response = await searchCollection(name, { query, filters, limit });
    took = response.took_ms;
    total = response.total;
    records = response.results.map((result) => ({
      id: result.id,
      data: result.record,
      score: result.score,
      files: result.files,
    }));
  } else {
    const response = await fetchCollectionRecords(name, { limit, offset, filters });
    total = response.total;
    records = response.results.map((item) => ({
      id: typeof item.id === "string" ? item.id : String(item.id ?? ""),
      data: item,
    }));
  }

  const totalPages = Math.max(1, Math.ceil(Math.max(total, records.length) / limit));

  return (
    <div className="container space-y-8 py-10">
      <nav className="flex items-center gap-2 text-[0.7rem] uppercase tracking-[0.35em] text-muted-foreground">
        <Link href={`/databases/${database}/collections`} className="hover:text-primary">
          {database}
        </Link>
        <span>/</span>
        <span className="text-primary">{name}</span>
      </nav>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-4">
          <Card>
            <CardHeader className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <div className="terminal-heading">Record Monitor</div>
                  <CardTitle className="text-lg text-primary">Operational Stream</CardTitle>
                  <CardDescription>Run hybrid lookups and inspect relational payloads.</CardDescription>
                </div>
                <AddRecordDialog collection={name} database={database} fields={schemaFields} />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex-1 min-w-[300px]">
                  <RecordsToolbar />
                </div>
                <FiltersWrapper fields={schemaFields} />
              </div>
              {(searchMode || filterMode) && (
                <div className="space-y-1">
                  {searchMode && (
                    <p className="text-[0.7rem] uppercase tracking-[0.25em] text-muted-foreground">
                      Query <span className="text-primary">{query}</span>
                      {typeof took === "number" ? ` · ${took.toFixed(1)} ms` : ""}
                    </p>
                  )}
                  {filterMode && (
                    <p className="text-[0.7rem] uppercase tracking-[0.25em] text-muted-foreground">
                      Filters <span className="text-primary">{Object.keys(filters).length} active</span>
                    </p>
                  )}
                </div>
              )}
              <RecordsTable collection={name} database={database} fields={viewFields} records={records} searchMode={searchMode} />
              <PaginationControls page={page} totalPages={totalPages} />
            </CardContent>
          </Card>
        </div>

        <aside className="space-y-4">
          <Card>
            <CardHeader className="space-y-2">
              <div className="terminal-heading">Schema Overview</div>
              <CardTitle className="text-primary">Collection Profile</CardTitle>
              <CardDescription>{schema.description ?? "No description provided."}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs uppercase tracking-[0.25em] text-muted-foreground">
              <div className="grid grid-cols-2 gap-3 text-foreground">
                <div className="space-y-1">
                  <span className="terminal-heading text-muted-foreground/70">Fields</span>
                  <span className="font-mono text-base text-primary">{schemaFields.length}</span>
                </div>
                <div className="space-y-1">
                  <span className="terminal-heading text-muted-foreground/70">Vector</span>
                  <span className="font-mono text-base text-primary">
                    {schemaFields.filter((field) => field.vectorize).length}
                  </span>
                </div>
                <div className="space-y-1">
                  <span className="terminal-heading text-muted-foreground/70">Config</span>
                  <span className="font-mono text-base text-primary">{Object.keys(schema.config ?? {}).length}</span>
                </div>
                <div className="space-y-1">
                  <span className="terminal-heading text-muted-foreground/70">Stores</span>
                  <span className="font-mono text-base text-primary">
                    {[...new Set(schemaFields.flatMap((field) => field.store_in ?? []))].length}
                  </span>
                </div>
              </div>
              <div className="terminal-divider" />
              <div className="space-y-2">
                <p className="terminal-heading">Storage Targets</p>
                <div className="flex flex-wrap gap-2">
                  {[...new Set(schemaFields.flatMap((field) => field.store_in ?? []))].map((store) => (
                    <Badge key={store} variant="outline">
                      {store}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="space-y-2">
              <div className="terminal-heading">Field Matrix</div>
              <CardTitle className="text-primary">Declared Attributes</CardTitle>
              <CardDescription>Flags denote enabled capabilities per field.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-muted-foreground">
              {schemaFields.map((field) => (
                <div key={field.name} className="rounded-md border border-border/60 bg-secondary/30 px-3 py-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm text-primary">{field.name}</span>
                    <Badge variant="outline">{field.type}</Badge>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {field.required ? <Badge variant="secondary">required</Badge> : null}
                    {field.indexed ? <Badge variant="secondary">indexed</Badge> : null}
                    {field.unique ? <Badge variant="secondary">unique</Badge> : null}
                    {field.vectorize ? <Badge variant="secondary">vectorized</Badge> : null}
                    {field.filterable ? <Badge variant="secondary">filterable</Badge> : null}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}
