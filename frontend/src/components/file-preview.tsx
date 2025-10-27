"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Download, FileIcon, ImageIcon } from "lucide-react";

interface FilePreviewProps {
  fieldName: string;
  filePath: string;
  collectionName: string;
  recordId: string;
}

export function FilePreview({ fieldName, filePath, collectionName, recordId }: FilePreviewProps) {
  const [imageError, setImageError] = useState(false);

  // Extract filename from path
  const filename = filePath.split("/").pop() || fieldName;
  const fileExtension = filename.split(".").pop()?.toLowerCase() || "";

  // Determine file type
  const imageExtensions = ["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp"];
  const pdfExtensions = ["pdf"];

  const isImage = imageExtensions.includes(fileExtension);
  const isPdf = pdfExtensions.includes(fileExtension);

  // Generate gateway URL
  const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000";
  const fileUrl = `${gatewayUrl}/files/${collectionName}/${recordId}/${filename}`;

  const handleDownload = () => {
    // Open in new tab instead of downloading
    window.open(fileUrl, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="space-y-3">
      {/* File Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isImage ? (
            <ImageIcon className="h-4 w-4 text-muted-foreground" />
          ) : (
            <FileIcon className="h-4 w-4 text-muted-foreground" />
          )}
          <div>
            <p className="text-xs font-mono text-primary">{fieldName}</p>
            <p className="text-[0.7rem] text-muted-foreground">{filename}</p>
          </div>
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={handleDownload}
          className="gap-2"
        >
          <Download className="h-3 w-3" />
          Download
        </Button>
      </div>

      {/* File Preview */}
      <div className="terminal-divider" />

      {isImage && !imageError ? (
        <div className="relative w-full aspect-video bg-secondary/40 rounded-md overflow-hidden">
          <img
            src={fileUrl}
            alt={filename}
            className="w-full h-full object-contain"
            onError={() => setImageError(true)}
          />
        </div>
      ) : isPdf ? (
        <div className="relative w-full aspect-[3/4] bg-secondary/40 rounded-md overflow-hidden">
          <iframe
            src={fileUrl}
            className="w-full h-full border-0"
            title={filename}
          />
        </div>
      ) : (
        <div className="flex items-center justify-center p-8 bg-secondary/40 rounded-md">
          <div className="text-center space-y-2">
            <FileIcon className="h-12 w-12 mx-auto text-muted-foreground/50" />
            <p className="text-xs text-muted-foreground">
              Preview not available for .{fileExtension} files
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
