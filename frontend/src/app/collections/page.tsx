import Link from "next/link";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { fetchCollections } from "@/lib/cortex-client";
import { formatDate } from "@/lib/format";
import { CollectionSearch } from "@/components/collection-search";
import { SchemaField } from "@/lib/types";

interface Props {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function CollectionsPage({ searchParams }: Props) {
  const params = await searchParams;
  const query = typeof params.q === "string" ? params.q : params.q?.[0] ?? "";

  const collections = await fetchCollections();
  const filtered = query
    ? collections.filter((collection) =>
        collection.name.toLowerCase().includes(query.toLowerCase()) ||
        (collection.schema?.description ?? "")
          .toLowerCase()
          .includes(query.toLowerCase())
      )
    : collections;

  return (
    <div className="container space-y-8 py-10">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold text-primary">Collections Registry</h1>
          <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
            {collections.length === 0
              ? "No collections registered"
              : `${collections.length} ACTIVE / ${filtered.length} VISIBLE`}
          </p>
        </div>
        <div className="flex w-full flex-col gap-2 sm:flex-row sm:items-center sm:justify-end">
          <CollectionSearch className="w-full max-w-sm" />
          <Button asChild size="sm" variant="secondary">
            <Link href="/collections/new">New Collection</Link>
          </Button>
          <Button asChild size="sm" variant="ghost">
            <Link href="/settings/embeddings">Embedding Settings</Link>
          </Button>
        </div>
      </div>

      {filtered.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No matching collections</CardTitle>
            <CardDescription>
              Try adjusting your search filters or clear the search textbox.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((collection) => {
            const fields = ((collection.schema?.fields as SchemaField[] | undefined) ?? []);
            const fieldCount = fields.length;
            const vectorizedCount = fields.filter((field) => field.vectorize).length ?? 0;
            return (
              <Card key={collection.name} className="flex flex-col">
                <CardHeader className="space-y-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold text-primary">
                      <Link href={`/collections/${collection.name}`}>{collection.name}</Link>
                    </CardTitle>
                    <Badge variant={vectorizedCount ? "secondary" : "outline"}>
                      {vectorizedCount.toString().padStart(2, "0")} • VECTOR
                    </Badge>
                  </div>
                  <CardDescription className="text-xs text-muted-foreground">
                    {collection.schema?.description ?? "No description provided."}
                  </CardDescription>
                </CardHeader>
                <CardContent className="mt-auto grid gap-2 text-xs text-muted-foreground">
                  <div className="flex items-center justify-between">
                    <span className="terminal-heading text-muted-foreground/70">Fields</span>
                    <span className="font-mono text-sm text-foreground">{fieldCount}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="terminal-heading text-muted-foreground/70">Updated</span>
                    <span className="font-mono text-[0.7rem] text-foreground/80">{formatDate(collection.updated_at)}</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {fields.slice(0, 4).map((field) => (
                      <Badge key={field.name} variant={field.vectorize ? "secondary" : "outline"}>
                        {field.name}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
