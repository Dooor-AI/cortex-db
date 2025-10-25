import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md border border-border/60 bg-transparent text-xs font-semibold uppercase tracking-[0.25em] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "border-border text-foreground hover:bg-secondary/40 hover:text-foreground",
        destructive: "border-destructive/70 text-destructive shadow-sm hover:bg-destructive/10",
        outline: "border-border text-muted-foreground hover:text-foreground",
        secondary: "border-border bg-secondary/40 text-foreground hover:bg-secondary/60",
        ghost: "border-transparent text-muted-foreground hover:text-foreground",
        link: "border-none text-foreground underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-6",
        sm: "h-8 rounded-md px-4 text-[0.65rem]",
        lg: "h-11 rounded-md px-8",
        icon: "h-9 w-9 px-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
