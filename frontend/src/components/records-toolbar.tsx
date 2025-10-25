"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface RecordsToolbarProps {
  className?: string;
  limitOptions?: number[];
}

export function RecordsToolbar({ className, limitOptions = [10, 20, 50] }: RecordsToolbarProps) {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [search, setSearch] = useState(searchParams.get("q") ?? "");
  const [limit, setLimit] = useState(Number(searchParams.get("limit") ?? 20));

  useEffect(() => {
    setSearch(searchParams.get("q") ?? "");
    setLimit(Number(searchParams.get("limit") ?? 20));
  }, [searchParams]);

  const updateParams = useMemo(
    () =>
      debounce((next: { q?: string; limit?: number }) => {
        const params = new URLSearchParams(searchParams.toString());
        if (next.q !== undefined) {
          if (next.q) params.set("q", next.q);
          else params.delete("q");
        }
        if (next.limit !== undefined) {
          params.set("limit", String(next.limit));
          params.delete("page");
        }
        router.push(`?${params.toString()}`);
      }, 250),
    [router, searchParams]
  );

  return (
    <div className={cn("flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between", className)}>
      <div className="relative w-full max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Semantic search"
          className="pl-9"
          value={search}
          onChange={(event) => {
            const next = event.target.value;
            setSearch(next);
            updateParams({ q: next });
          }}
        />
      </div>
      <div className="flex items-center gap-2 text-[0.7rem] uppercase tracking-[0.25em] text-muted-foreground">
        <span>Rows</span>
        <select
          className="h-9 rounded-md border border-border/60 bg-secondary/40 px-3 text-xs uppercase tracking-[0.25em] text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary"
          value={limit}
          onChange={(event) => {
            const next = Number(event.target.value);
            setLimit(next);
            updateParams({ limit: next });
          }}
        >
          {limitOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

function debounce<T extends (...args: any[]) => void>(fn: T, delay: number) {
  let timer: ReturnType<typeof setTimeout> | undefined;
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}
