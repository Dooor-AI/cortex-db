import Link from "next/link";

import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { formatDate, truncate } from "@/lib/format";

export interface FieldSummary {
  name: string;
  type: string;
}

export interface RecordRow {
  id?: string;
  data: Record<string, unknown>;
  score?: number;
  files?: Record<string, string>;
  created_at?: string;
  updated_at?: string;
}

interface RecordsTableProps {
  collection: string;
  fields: FieldSummary[];
  records: RecordRow[];
  searchMode?: boolean;
}

export function RecordsTable({ collection, fields, records, searchMode }: RecordsTableProps) {
  const columns = fields.slice(0, 4);

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[160px]">Record ID</TableHead>
            {columns.map((field) => (
              <TableHead key={field.name} className="capitalize">
                {field.name}
              </TableHead>
            ))}
            {searchMode ? <TableHead className="w-[100px] text-right">Score</TableHead> : null}
            <TableHead className="w-[120px] text-right">Updated</TableHead>
            <TableHead className="w-[80px]" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {records.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.length + 4} className="text-center text-muted-foreground">
                No records found.
              </TableCell>
            </TableRow>
          ) : (
            records.map((row, index) => {
              const identifier = row.id ?? (row.data.id as string | number | undefined);
              const key = identifier !== undefined ? String(identifier) : `row-${index}`;
              return (
                <TableRow key={key}>
                  <TableCell className="font-mono text-xs">
                    {identifier ?? "—"}
                  </TableCell>
                  {columns.map((field) => (
                    <TableCell key={field.name} className="max-w-xs truncate text-sm">
                      {renderCell(row.data[field.name])}
                    </TableCell>
                  ))}
                  {searchMode ? (
                    <TableCell className="text-right text-sm font-medium">
                      {row.score ? row.score.toFixed(3) : "—"}
                    </TableCell>
                  ) : null}
                  <TableCell className="text-right text-xs text-muted-foreground">
                    {formatDate((row.data.updated_at as string) ?? row.updated_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    {identifier ? (
                      <Button variant="ghost" size="sm" asChild>
                        <Link href={`/collections/${collection}/records/${identifier}`}>
                          View
                        </Link>
                      </Button>
                    ) : null}
                  </TableCell>
                </TableRow>
              );
            })
          )}
        </TableBody>
        <TableCaption>
          Displaying {records.length} record{records.length === 1 ? "" : "s"}
        </TableCaption>
      </Table>
    </div>
  );
}

function renderCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return truncate(value, 120);
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return value.length ? `${value.length} item(s)` : "[]";
  if (value instanceof Date) return formatDate(value.toISOString());
  try {
    return truncate(JSON.stringify(value));
  } catch (error) {
    return "[object]";
  }
}
