import Link from "next/link";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { fetchCollections } from "@/lib/cortex-client";
import { formatDate } from "@/lib/format";
import { SchemaField } from "@/lib/types";

function buildSeries(values: number[]): { path: string; markers: { x: number; y: number }[] } {
  if (values.length === 0) {
    return { path: "", markers: [] };
  }
  const max = Math.max(...values, 1);
  const points = values.map((value, index) => {
    const x = values.length === 1 ? 0 : (index / (values.length - 1)) * 100;
    const y = 100 - (value / max) * 100;
    return { x, y };
  });
  const path = points
    .map(({ x, y }, index) => `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`)
    .join(" ");
  return { path, markers: points };
}

export default async function Home() {
  const collections = await fetchCollections();

  const totalCollections = collections.length;
  const totalFields = collections.reduce(
    (acc, item) => acc + ((item.schema?.fields?.length as number | undefined) ?? 0),
    0
  );
  const vectorFields = collections.reduce((acc, item) => {
    const fields = ((item.schema?.fields as SchemaField[] | undefined) ?? []);
    return acc + fields.filter((field) => field.vectorize).length;
  }, 0);

  const activityLog = collections
    .flatMap((collection) =>
      ((collection.schema?.fields as SchemaField[] | undefined) ?? [])
        .slice(0, 2)
        .map((field) => ({
          collection: collection.name,
          field: field.name,
          type: field.type,
        }))
    )
    .slice(0, 6);

  const vectorSeries = buildSeries(
    collections.map((collection) => {
      const fields = (collection.schema?.fields as SchemaField[] | undefined) ?? [];
      return fields.filter((field) => field.vectorize).length + 1;
    })
  );

  return (
    <div className="container space-y-10 py-10">
      <section className="grid gap-6 xl:grid-cols-[2fr_3fr]">
        <Card className="terminal-card">
          <CardHeader className="pb-2">
            <div className="terminal-heading">Agent Allocation</div>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid grid-cols-3 gap-6">
              {[{ label: "Collections", value: totalCollections }, { label: "Fields", value: totalFields }, {
                label: "Vector Fields",
                value: vectorFields,
              }].map((item) => (
                <div key={item.label} className="space-y-1">
                  <p className="terminal-heading text-[0.65rem] tracking-[0.45em] text-muted-foreground/70">
                    {item.label}
                  </p>
                  <p className="terminal-metric">{item.value.toString().padStart(3, "0")}</p>
                </div>
              ))}
            </div>
            <div className="terminal-divider" />
            <div className="space-y-2">
              <div className="terminal-heading">Activity Log</div>
              <div className="space-y-2 text-[0.75rem] text-muted-foreground">
                {activityLog.length === 0 ? (
                  <p>No schema activity detected.</p>
                ) : (
                  activityLog.map((entry, index) => (
                    <p key={`${entry.collection}-${entry.field}-${index}`} className="flex items-center gap-2">
                      <span className="text-primary">{new Date().toISOString().slice(11, 19)}</span>
                      <span>
                        <span className="text-primary/90">{entry.collection}</span> registered field
                        <span className="text-primary/70"> {entry.field}</span> ({entry.type})
                      </span>
                    </p>
                  ))
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="terminal-card">
          <CardHeader className="space-y-1">
            <div className="terminal-heading">Mission Activity Overview</div>
            <CardDescription className="text-xs text-muted-foreground">
              Vectorized field throughput per collection snapshot.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="h-56 w-full rounded-lg border border-border/60 bg-secondary/30 p-4">
              {vectorSeries.path ? (
                <svg viewBox="0 0 100 100" className="h-full w-full" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="vectorGradient" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="rgba(255,255,255,0.25)" />
                      <stop offset="100%" stopColor="rgba(255,255,255,0.03)" />
                    </linearGradient>
                  </defs>
                  <rect width="100" height="100" fill="rgba(10,10,12,0.85)" />
                  <path
                    d={`${vectorSeries.path} L100,100 L0,100 Z`}
                    fill="url(#vectorGradient)"
                    stroke="rgba(255,255,255,0.35)"
                    strokeWidth="0.6"
                  />
                  <path
                    d={vectorSeries.path}
                    fill="none"
                    stroke="rgba(255,255,255,0.85)"
                    strokeWidth="1.2"
                    strokeLinejoin="round"
                    strokeLinecap="round"
                  />
                  {vectorSeries.markers.map((point, index) => (
                    <circle key={index} cx={point.x} cy={point.y} r={1.2} fill="rgba(255,255,255,0.9)" />
                  ))}
                </svg>
              ) : (
                <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                  Awaiting collection telemetry…
                </div>
              )}
            </div>
            <div className="grid gap-3 text-xs text-muted-foreground md:grid-cols-2">
              <div className="space-y-1 rounded-md border border-border/60 bg-secondary/30 p-3">
                <p className="terminal-heading">Successful Operations</p>
                <p className="text-foreground">Vector ready fields: {vectorFields}</p>
                <p className="text-foreground/60">Median per collection: {totalCollections ? Math.round(vectorFields / totalCollections) : 0}</p>
              </div>
              <div className="space-y-1 rounded-md border border-border/60 bg-secondary/30 p-3">
                <p className="terminal-heading">Pending Operations</p>
                <p className="text-foreground">Non-vector fields: {totalFields - vectorFields}</p>
                <p className="text-foreground/60">Review schema to enable embeddings.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-2">
          <h2 className="terminal-heading text-muted-foreground">Collection Manifest</h2>
          <div className="flex items-center gap-2">
            <Button asChild variant="secondary" size="sm">
              <Link href="/collections/new">New Collection</Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href="/collections">Open Registry</Link>
            </Button>
            <Button asChild variant="ghost" size="sm">
              <Link href="/settings/embeddings">Embedding Settings</Link>
            </Button>
          </div>
        </div>

        {collections.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>No collections detected</CardTitle>
              <CardDescription>
                Create a schema via the CortexDB API to see it appear here. Check <code>schemas/</code> for examples.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-0">
              <div className="overflow-hidden rounded-lg">
                <table className="w-full text-left">
                  <thead className="bg-secondary/40 text-[0.6rem] uppercase tracking-[0.25em] text-muted-foreground">
                    <tr className="border-b border-border/60">
                      <th className="px-4 py-3">Collection</th>
                      <th className="px-4 py-3">Fields</th>
                      <th className="px-4 py-3">Vector</th>
                      <th className="px-4 py-3">Updated</th>
                    </tr>
                  </thead>
                  <tbody className="text-[0.8rem]">
                    {collections.slice(0, 8).map((collection) => {
              const fields = ((collection.schema?.fields as SchemaField[] | undefined) ?? []);
              const vectorized = fields.filter((field) => field.vectorize).length;
                      return (
                        <tr key={collection.name} className="border-b border-border/40 transition-colors hover:bg-muted/20">
                          <td className="px-4 py-3 font-mono text-xs text-primary">
                            <Link href={`/collections/${collection.name}`}>{collection.name}</Link>
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">{fields.length}</td>
                          <td className="px-4 py-3 text-muted-foreground">{vectorized}</td>
                          <td className="px-4 py-3 text-muted-foreground">{formatDate(collection.updated_at)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </section>
    </div>
  );
}
