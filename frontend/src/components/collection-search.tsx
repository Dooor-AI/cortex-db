"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Search, X } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function CollectionSearch({ className }: { className?: string }) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [value, setValue] = useState(searchParams.get("q") ?? "");

  useEffect(() => {
    setValue(searchParams.get("q") ?? "");
  }, [searchParams]);

  const updateQuery = useMemo(
    () =>
      debounce((next: string) => {
        const params = new URLSearchParams(searchParams.toString());
        if (next) {
          params.set("q", next);
        } else {
          params.delete("q");
        }
        router.push(`?${params.toString()}`);
      }, 300),
    [router, searchParams]
  );

  const onChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const next = event.target.value;
      setValue(next);
      updateQuery(next);
    },
    [updateQuery]
  );

  const clear = () => {
    setValue("");
    updateQuery("");
  };

  return (
    <div className={cn("relative flex items-center", className)}>
      <Search className="pointer-events-none absolute left-3 h-4 w-4 text-muted-foreground/80" />
      <Input
        value={value}
        onChange={onChange}
        placeholder="Search"
        className="pl-9 pr-10"
      />
      {value && (
        <Button variant="ghost" size="icon" className="absolute right-1 h-7 w-7" onClick={clear}>
          <X className="h-4 w-4" />
        </Button>
      )}
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
