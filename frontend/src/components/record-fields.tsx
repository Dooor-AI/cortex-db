import { Badge } from "@/components/ui/badge";
import { SchemaField } from "@/lib/types";

interface RecordFieldsProps {
  record: Record<string, unknown>;
  schemaFields: SchemaField[];
  files: Record<string, string>;
}

export function RecordFields({ record, schemaFields, files }: RecordFieldsProps) {
  // Filter out system fields and file fields
  const displayFields = schemaFields.filter(
    (field) => !["id", "created_at", "updated_at"].includes(field.name)
  );

  if (displayFields.length === 0) {
    return <p className="text-sm text-muted-foreground">No fields to display.</p>;
  }

  return (
    <div className="space-y-4">
      {displayFields.map((field) => {
        const value = record[field.name];
        const isFile = field.name in files;

        // Skip if value is null/undefined
        if (value === null || value === undefined) return null;

        return (
          <div key={field.name} className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="terminal-heading text-sm">{field.name}</span>
              <Badge variant="outline" className="text-[0.65rem]">
                {field.type}
              </Badge>
              {field.vectorize && (
                <Badge variant="secondary" className="text-[0.65rem]">
                  vectorized
                </Badge>
              )}
              {isFile && (
                <Badge variant="secondary" className="text-[0.65rem]">
                  file
                </Badge>
              )}
            </div>
            <div className="rounded-md border border-border/60 bg-secondary/40 p-3">
              {isFile ? (
                <p className="text-xs font-mono text-muted-foreground break-all">
                  {String(value)}
                </p>
              ) : typeof value === "string" && value.length > 200 ? (
                <p className="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap">
                  {value}
                </p>
              ) : (
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {String(value)}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
