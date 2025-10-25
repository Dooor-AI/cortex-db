"use client";

import { useState } from "react";
import { Plus, X, Filter } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { SchemaField } from "@/lib/types";
import { Badge } from "@/components/ui/badge";

interface FilterCondition {
  id: string;
  field: string;
  operator: string;
  value: string;
}

interface AdvancedFiltersProps {
  fields: SchemaField[];
  onApplyFilters: (filters: Record<string, any>) => void;
  currentFilters?: Record<string, any>;
}

const OPERATORS = {
  string: [
    { value: "$eq", label: "equals" },
    { value: "$ne", label: "not equals" },
  ],
  text: [
    { value: "$eq", label: "equals" },
    { value: "$ne", label: "not equals" },
  ],
  int: [
    { value: "$eq", label: "equals" },
    { value: "$ne", label: "not equals" },
    { value: "$gt", label: "greater than" },
    { value: "$gte", label: "greater or equal" },
    { value: "$lt", label: "less than" },
    { value: "$lte", label: "less or equal" },
  ],
  float: [
    { value: "$eq", label: "equals" },
    { value: "$ne", label: "not equals" },
    { value: "$gt", label: "greater than" },
    { value: "$gte", label: "greater or equal" },
    { value: "$lt", label: "less than" },
    { value: "$lte", label: "less or equal" },
  ],
  boolean: [{ value: "$eq", label: "equals" }],
  date: [
    { value: "$eq", label: "equals" },
    { value: "$ne", label: "not equals" },
    { value: "$gt", label: "after" },
    { value: "$gte", label: "on or after" },
    { value: "$lt", label: "before" },
    { value: "$lte", label: "on or before" },
  ],
  datetime: [
    { value: "$eq", label: "equals" },
    { value: "$ne", label: "not equals" },
    { value: "$gt", label: "after" },
    { value: "$gte", label: "on or after" },
    { value: "$lt", label: "before" },
    { value: "$lte", label: "on or before" },
  ],
  enum: [
    { value: "$eq", label: "equals" },
    { value: "$ne", label: "not equals" },
  ],
};

export function AdvancedFilters({ fields, onApplyFilters, currentFilters = {} }: AdvancedFiltersProps) {
  const [open, setOpen] = useState(false);
  const [conditions, setConditions] = useState<FilterCondition[]>([]);

  // Filter fields that can be filtered (exclude files, arrays, system fields)
  const filterableFields = fields.filter(
    (f) => f.type !== "file" && f.type !== "array" && !["id", "created_at", "updated_at"].includes(f.name.toLowerCase())
  );

  const activeFilterCount = Object.keys(currentFilters).length;

  const addCondition = () => {
    const newCondition: FilterCondition = {
      id: Math.random().toString(36).slice(2),
      field: filterableFields[0]?.name || "",
      operator: "$eq",
      value: "",
    };
    setConditions([...conditions, newCondition]);
  };

  const removeCondition = (id: string) => {
    setConditions(conditions.filter((c) => c.id !== id));
  };

  const updateCondition = (id: string, updates: Partial<FilterCondition>) => {
    setConditions(
      conditions.map((c) => {
        if (c.id !== id) return c;
        const updated = { ...c, ...updates };
        // Reset operator if field type changed
        if (updates.field && updates.field !== c.field) {
          const field = filterableFields.find((f) => f.name === updates.field);
          if (field) {
            const operators = OPERATORS[field.type as keyof typeof OPERATORS] || OPERATORS.string;
            updated.operator = operators[0].value;
          }
        }
        return updated;
      })
    );
  };

  const buildFilters = (): Record<string, any> => {
    const filters: Record<string, any> = {};
    for (const condition of conditions) {
      if (!condition.field || !condition.value) continue;

      const field = filterableFields.find((f) => f.name === condition.field);
      if (!field) continue;

      // Parse value based on field type
      let parsedValue: any = condition.value;
      if (field.type === "int") {
        parsedValue = parseInt(condition.value, 10);
        if (isNaN(parsedValue)) continue;
      } else if (field.type === "float") {
        parsedValue = parseFloat(condition.value);
        if (isNaN(parsedValue)) continue;
      } else if (field.type === "boolean") {
        parsedValue = condition.value === "true";
      }

      // Build filter structure
      if (condition.operator === "$eq") {
        filters[condition.field] = parsedValue;
      } else {
        filters[condition.field] = { [condition.operator]: parsedValue };
      }
    }
    return filters;
  };

  const handleApply = () => {
    const filters = buildFilters();
    onApplyFilters(filters);
    setOpen(false);
  };

  const handleClear = () => {
    setConditions([]);
    onApplyFilters({});
    setOpen(false);
  };

  const getFieldInputType = (field: SchemaField): string => {
    switch (field.type) {
      case "int":
      case "float":
        return "number";
      case "date":
        return "date";
      case "datetime":
        return "datetime-local";
      case "boolean":
        return "select";
      case "enum":
        return "select";
      default:
        return "text";
    }
  };

  const renderValueInput = (condition: FilterCondition) => {
    const field = filterableFields.find((f) => f.name === condition.field);
    if (!field) return null;

    const inputType = getFieldInputType(field);

    if (inputType === "select") {
      if (field.type === "boolean") {
        return (
          <select
            value={condition.value}
            onChange={(e) => updateCondition(condition.id, { value: e.target.value })}
            className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">Select...</option>
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        );
      } else if (field.type === "enum" && field.values) {
        return (
          <select
            value={condition.value}
            onChange={(e) => updateCondition(condition.id, { value: e.target.value })}
            className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <option value="">Select...</option>
            {field.values.map((val) => (
              <option key={String(val)} value={String(val)}>
                {String(val)}
              </option>
            ))}
          </select>
        );
      }
    }

    return (
      <Input
        type={inputType}
        value={condition.value}
        onChange={(e) => updateCondition(condition.id, { value: e.target.value })}
        placeholder="Enter value"
        step={field.type === "float" ? "any" : undefined}
      />
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="relative">
          <Filter className="mr-2 h-4 w-4" />
          Filters
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="ml-2 h-5 min-w-5 px-1 text-xs">
              {activeFilterCount}
            </Badge>
          )}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] max-w-3xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Advanced Filters</DialogTitle>
          <DialogDescription>
            Create SQL filters to query records. All conditions are combined with AND logic.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {conditions.length === 0 ? (
            <div className="rounded-md border border-dashed border-border/60 p-8 text-center text-sm text-muted-foreground">
              No filters added yet. Click "Add Filter" to create a condition.
            </div>
          ) : (
            <div className="space-y-3">
              {conditions.map((condition, index) => {
                const field = filterableFields.find((f) => f.name === condition.field);
                const operators = field ? OPERATORS[field.type as keyof typeof OPERATORS] || OPERATORS.string : [];

                return (
                  <div key={condition.id} className="grid grid-cols-[1fr_1fr_1fr_auto] items-end gap-3 rounded-md border border-border/60 bg-secondary/30 p-3">
                    <div className="space-y-2">
                      <Label className="text-xs uppercase tracking-wider text-muted-foreground">Field</Label>
                      <select
                        value={condition.field}
                        onChange={(e) => updateCondition(condition.id, { field: e.target.value })}
                        className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        {filterableFields.map((f) => (
                          <option key={f.name} value={f.name}>
                            {f.name} ({f.type})
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs uppercase tracking-wider text-muted-foreground">Operator</Label>
                      <select
                        value={condition.operator}
                        onChange={(e) => updateCondition(condition.id, { operator: e.target.value })}
                        className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        {operators.map((op) => (
                          <option key={op.value} value={op.value}>
                            {op.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs uppercase tracking-wider text-muted-foreground">Value</Label>
                      {renderValueInput(condition)}
                    </div>

                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeCondition(condition.id)}
                      className="h-9 w-9 text-muted-foreground hover:text-destructive"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                );
              })}
            </div>
          )}

          <Button variant="outline" size="sm" onClick={addCondition} className="w-full" disabled={filterableFields.length === 0}>
            <Plus className="mr-2 h-4 w-4" />
            Add Filter
          </Button>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="ghost" onClick={handleClear}>
            Clear All
          </Button>
          <Button variant="secondary" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleApply}>Apply Filters</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
