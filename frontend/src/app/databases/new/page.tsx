"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiRequest } from "@/lib/cortex-client";

export default function NewDatabasePage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const payload = {
        name,
        description: description || undefined,
        metadata: {},
      };

      await apiRequest("/databases", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      router.refresh(); // Force refresh to clear cache
      router.push("/databases");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create database");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container max-w-2xl space-y-8 py-10">
      <div className="space-y-1">
        <h1 className="text-3xl font-semibold text-primary">New Database</h1>
        <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
          CREATE A NEW DATABASE INSTANCE
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
          <CardDescription>
            Create a new database to organize your collections. Each database is isolated
            with its own PostgreSQL database, Qdrant collections, and MinIO buckets.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name">Database Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="my_database"
                pattern="^[a-z][a-z0-9_]*$"
                title="Must start with lowercase letter, contain only lowercase letters, numbers, and underscores"
                required
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground">
                Must start with a lowercase letter and contain only lowercase letters, numbers,
                and underscores (max 63 characters)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Description of this database..."
                rows={3}
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground">
                Optional description to help identify this database
              </p>
            </div>

            {error && (
              <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <div className="flex items-center gap-2">
              <Button type="submit" disabled={loading}>
                {loading ? "Creating..." : "Create Database"}
              </Button>
              <Button type="button" variant="ghost" asChild disabled={loading}>
                <Link href="/databases">Cancel</Link>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
