"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

interface VectorChunk {
  id: string;
  field: string;
  chunk_index: number;
  text: string;
}

interface VectorChunksProps {
  collectionName: string;
  recordId: string;
}

export function VectorChunks({ collectionName, recordId }: VectorChunksProps) {
  const [chunks, setChunks] = useState<VectorChunk[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchVectors = async () => {
      try {
        const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000";
        const response = await fetch(
          `${gatewayUrl}/collections/${collectionName}/records/${recordId}/vectors`
        );

        if (!response.ok) {
          throw new Error("Failed to fetch vectors");
        }

        const data = await response.json();
        setChunks(data.vectors || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchVectors();
  }, [collectionName, recordId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || chunks.length === 0) {
    return null; // Don't show anything if no vectors or error
  }

  return (
    <div className="space-y-4">
      {chunks.map((chunk) => (
        <div
          key={chunk.id}
          className="space-y-2 rounded-md border border-border/60 bg-secondary/40 p-4"
        >
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="font-mono text-[0.7rem]">
              {chunk.field}
            </Badge>
            <Badge variant="secondary" className="text-[0.7rem]">
              Chunk #{chunk.chunk_index}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap">
            {chunk.text}
          </p>
        </div>
      ))}
    </div>
  );
}
