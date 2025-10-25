"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { AdvancedFilters } from "./advanced-filters";
import { SchemaField } from "@/lib/types";

interface FiltersWrapperProps {
  fields: SchemaField[];
}

export function FiltersWrapper({ fields }: FiltersWrapperProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Parse current filters from URL
  let currentFilters: Record<string, any> = {};
  const filtersParam = searchParams.get("filters");
  if (filtersParam) {
    try {
      currentFilters = JSON.parse(filtersParam);
    } catch {
      // Invalid JSON, ignore
    }
  }

  const handleApplyFilters = (filters: Record<string, any>) => {
    const params = new URLSearchParams(searchParams.toString());

    if (Object.keys(filters).length > 0) {
      params.set("filters", JSON.stringify(filters));
    } else {
      params.delete("filters");
    }

    // Reset to page 1 when applying new filters
    params.delete("page");

    router.push(`?${params.toString()}`);
  };

  return (
    <AdvancedFilters
      fields={fields}
      onApplyFilters={handleApplyFilters}
      currentFilters={currentFilters}
    />
  );
}
