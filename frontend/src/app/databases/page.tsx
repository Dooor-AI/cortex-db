import Link from "next/link";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { fetchDatabases } from "@/lib/cortex-client";
import { formatDate } from "@/lib/format";

// Disable caching for this page to always show fresh data
export const revalidate = 0;

export default async function DatabasesPage() {
  const databases = await fetchDatabases();

  return (
    <div className="container space-y-8 py-10">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold text-primary">Databases</h1>
          <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
            {databases.length === 0
              ? "No databases created"
              : `${databases.length} ACTIVE`}
          </p>
        </div>
        <div className="flex w-full flex-col gap-2 sm:flex-row sm:items-center sm:justify-end">
          <Button asChild size="sm" variant="secondary">
            <Link href="/databases/new">New Database</Link>
          </Button>
        </div>
      </div>

      {databases.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No databases found</CardTitle>
            <CardDescription>
              Create your first database to start organizing your collections.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {databases.map((database) => {
            return (
              <Card key={database.id} className="flex flex-col">
                <CardHeader className="space-y-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg font-semibold text-primary">
                      <Link href={`/databases/${database.name}/collections`}>
                        {database.name}
                      </Link>
                    </CardTitle>
                  </div>
                  <CardDescription className="text-xs text-muted-foreground">
                    {database.description ?? "No description provided."}
                  </CardDescription>
                </CardHeader>
                <CardContent className="mt-auto grid gap-2 text-xs text-muted-foreground">
                  <div className="flex items-center justify-between">
                    <span className="terminal-heading text-muted-foreground/70">Created</span>
                    <span className="font-mono text-[0.7rem] text-foreground/80">
                      {formatDate(database.created_at)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="terminal-heading text-muted-foreground/70">Updated</span>
                    <span className="font-mono text-[0.7rem] text-foreground/80">
                      {formatDate(database.updated_at)}
                    </span>
                  </div>
                  <div className="mt-2">
                    <Button asChild size="sm" variant="outline" className="w-full">
                      <Link href={`/databases/${database.name}/collections`}>
                        View Collections
                      </Link>
                    </Button>
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
