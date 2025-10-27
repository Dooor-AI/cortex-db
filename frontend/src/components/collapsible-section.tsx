"use client";

import { ChevronDown, ChevronRight } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { useState } from "react";

interface CollapsibleSectionProps {
  title: string;
  description?: string;
  heading?: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

export function CollapsibleSection({
  title,
  description,
  heading,
  children,
  defaultOpen = false,
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card className="border-border/60">
        <CardHeader className="space-y-2">
          <CollapsibleTrigger className="flex w-full items-center justify-between hover:opacity-70 transition-opacity">
            <div className="flex items-center gap-2">
              {isOpen ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
              <div className="text-left space-y-1">
                {heading && <div className="terminal-heading">{heading}</div>}
                <CardTitle className="text-primary">{title}</CardTitle>
              </div>
            </div>
          </CollapsibleTrigger>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CollapsibleContent>
          <CardContent>{children}</CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}
