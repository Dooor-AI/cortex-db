"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { SchemaField } from "@/lib/types";

interface AddRecordDialogProps {
  collection: string;
  database: string;
  fields: SchemaField[];
}

export function AddRecordDialog({ collection, database, fields }: AddRecordDialogProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [files, setFiles] = useState<Record<string, File>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      let body: any;
      let headers: Record<string, string> = {};

      // Check if we have file uploads
      const hasFiles = Object.keys(files).length > 0;

      if (hasFiles) {
        // Use FormData for file uploads
        const formDataObj = new FormData();

        // Add regular fields as JSON strings
        for (const [key, value] of Object.entries(formData)) {
          if (value !== undefined && value !== "") {
            formDataObj.append(key, JSON.stringify(value));
          }
        }

        // Add files
        for (const [key, file] of Object.entries(files)) {
          formDataObj.append(key, file);
        }

        body = formDataObj;
      } else {
        // Use JSON for non-file data
        headers["Content-Type"] = "application/json";
        body = JSON.stringify(formData);
      }

      const res = await fetch(`http://localhost:8000/collections/${collection}/records`, {
        method: "POST",
        headers,
        body,
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || `Failed with status ${res.status}`);
      }

      // Success - close dialog and refresh
      setOpen(false);
      setFormData({});
      setFiles({});
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create record");
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (fieldName: string, value: any) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }));
  };

  const handleFileChange = (fieldName: string, file: File | null) => {
    if (file) {
      setFiles((prev) => ({ ...prev, [fieldName]: file }));
    } else {
      const newFiles = { ...files };
      delete newFiles[fieldName];
      setFiles(newFiles);
    }
  };

  const renderField = (field: SchemaField) => {
    const { name, type, required, description } = field;

    switch (type) {
      case "string":
        return (
          <div key={name} className="space-y-2">
            <Label htmlFor={name}>
              {name} {required && <span className="text-destructive">*</span>}
            </Label>
            <Input
              id={name}
              value={formData[name] || ""}
              onChange={(e) => handleFieldChange(name, e.target.value)}
              placeholder={description || `Enter ${name}`}
              required={required}
              disabled={loading}
            />
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
        );

      case "text":
        return (
          <div key={name} className="space-y-2">
            <Label htmlFor={name}>
              {name} {required && <span className="text-destructive">*</span>}
            </Label>
            <Textarea
              id={name}
              value={formData[name] || ""}
              onChange={(e) => handleFieldChange(name, e.target.value)}
              placeholder={description || `Enter ${name}`}
              required={required}
              disabled={loading}
              rows={4}
            />
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
        );

      case "int":
      case "float":
        return (
          <div key={name} className="space-y-2">
            <Label htmlFor={name}>
              {name} {required && <span className="text-destructive">*</span>}
            </Label>
            <Input
              id={name}
              type="number"
              step={type === "float" ? "any" : "1"}
              value={formData[name] ?? ""}
              onChange={(e) => handleFieldChange(name, e.target.value ? Number(e.target.value) : "")}
              placeholder={description || `Enter ${name}`}
              required={required}
              disabled={loading}
            />
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
        );

      case "boolean":
        return (
          <div key={name} className="flex items-center space-x-2">
            <input
              id={name}
              type="checkbox"
              checked={formData[name] || false}
              onChange={(e) => handleFieldChange(name, e.target.checked)}
              disabled={loading}
              className="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor={name} className="cursor-pointer">
              {name} {description && <span className="text-xs text-muted-foreground">- {description}</span>}
            </Label>
          </div>
        );

      case "date":
        return (
          <div key={name} className="space-y-2">
            <Label htmlFor={name}>
              {name} {required && <span className="text-destructive">*</span>}
            </Label>
            <Input
              id={name}
              type="date"
              value={formData[name] || ""}
              onChange={(e) => handleFieldChange(name, e.target.value)}
              required={required}
              disabled={loading}
            />
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
        );

      case "datetime":
        return (
          <div key={name} className="space-y-2">
            <Label htmlFor={name}>
              {name} {required && <span className="text-destructive">*</span>}
            </Label>
            <Input
              id={name}
              type="datetime-local"
              value={formData[name] || ""}
              onChange={(e) => handleFieldChange(name, e.target.value)}
              required={required}
              disabled={loading}
            />
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
        );

      case "file":
        return (
          <div key={name} className="space-y-2">
            <Label htmlFor={name}>
              {name} {required && <span className="text-destructive">*</span>}
            </Label>
            <Input
              id={name}
              type="file"
              onChange={(e) => handleFileChange(name, e.target.files?.[0] || null)}
              required={required}
              disabled={loading}
            />
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
            {files[name] && (
              <p className="text-xs text-primary">Selected: {files[name].name}</p>
            )}
          </div>
        );

      case "enum":
        return (
          <div key={name} className="space-y-2">
            <Label htmlFor={name}>
              {name} {required && <span className="text-destructive">*</span>}
            </Label>
            <select
              id={name}
              value={formData[name] || ""}
              onChange={(e) => handleFieldChange(name, e.target.value)}
              required={required}
              disabled={loading}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="">Select {name}</option>
              {field.values?.map((value) => (
                <option key={String(value)} value={String(value)}>
                  {String(value)}
                </option>
              ))}
            </select>
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
        );

      default:
        return (
          <div key={name} className="space-y-2">
            <Label htmlFor={name}>
              {name} {required && <span className="text-destructive">*</span>}
            </Label>
            <Input
              id={name}
              value={formData[name] || ""}
              onChange={(e) => handleFieldChange(name, e.target.value)}
              placeholder={description || `Enter ${name}`}
              required={required}
              disabled={loading}
            />
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
        );
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="secondary">
          Add Record
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add Record to {collection}</DialogTitle>
          <DialogDescription>
            Fill in the fields below to create a new record in this collection.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {fields
            .filter((f) => {
              // Skip array fields
              if (f.type === "array") return false;
              // Skip auto-generated system fields
              const systemFields = ["id", "created_at", "updated_at"];
              return !systemFields.includes(f.name.toLowerCase());
            })
            .map((field) => renderField(field))}

          {error && (
            <div className="rounded-md border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setOpen(false)} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create Record"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
