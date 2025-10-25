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
import { fetchDatabaseCollections } from "@/lib/cortex-client";
import { formatDate } from "@/lib/format";
import { SchemaField } from "@/lib/types";

interface Props {
  params: Promise<{ database: string }>;
}

// Disable caching for this page to always show fresh data
export const revalidate = 0;

export default async function DatabaseCollectionsPage({ params }: Props) {
  const { database } = await params;
  const collections = await fetchDatabaseCollections(database);

  return (
    <div className="container space-y-8 py-10">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Button asChild variant="ghost" size="sm">
              <Link href="/databases">← Databases</Link>
            </Button>
          </div>
          <h1 className="text-3xl font-semibold text-primary">
            {database} / Collections
          </h1>
          <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
            {collections.length === 0
              ? "No collections in this database"
              : `${collections.length} ACTIVE`}
          </p>
        </div>
        <div className="flex w-full flex-col gap-2 sm:flex-row sm:items-center sm:justify-end">
          <Button asChild size="sm" variant="secondary">
            <Link href={`/databases/${database}/collections/new`}>
              New Collection
            </Link>
          </Button>
        </div>
      </div>

      {collections.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No collections found</CardTitle>
            <CardDescription>
              Create your first collection in this database to start storing data.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {collections.map((collection) => {
            const fields = ((collection.schema?.fields as SchemaField[] | undefined) ?? []);
            const fieldCount = fields.length;
            const vectorizedCount = fields.filter((field) => field.vectorize).length ?? 0;
            return (
              <Card key={collection.name} className="flex flex-col">
                <CardHeader className="space-y-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold text-primary">
                      <Link href={`/databases/${database}/collections/${collection.name}`}>
                        {collection.name}
                      </Link>
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
                    <span className="font-mono text-[0.7rem] text-foreground/80">
                      {formatDate(collection.updated_at)}
                    </span>
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
