import type { Metadata } from "next";
import "./globals.css";

import { ThemeProvider } from "@/components/theme-provider";
import { ThemeToggle } from "@/components/theme-toggle";
import Link from "next/link";

export const metadata: Metadata = {
  title: "CortexDB Studio",
  description: "Visualize and manage CortexDB collections.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background font-mono antialiased">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
          <div className="flex min-h-screen flex-col">
            <header className="border-b border-border bg-background">
              <div className="container flex flex-col gap-5 py-6">
                <div className="flex flex-col gap-1 text-[0.65rem] uppercase tracking-[0.35em] text-muted-foreground">
                  <span>CortexDB Studio</span>
                  <span>Unified Data Operations Console</span>
                </div>
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div className="flex flex-wrap gap-6 text-[0.65rem] uppercase tracking-[0.35em] text-muted-foreground">
                    <span>Channel: LOCAL</span>
                    <span>Timestamp: {new Date().toISOString().replace("T", " ").slice(0, 19)}</span>
                  </div>
                  <nav className="flex items-center gap-3 text-[0.65rem] uppercase tracking-[0.35em] text-muted-foreground">
                    <Link href="/" className="border border-transparent px-3 py-2 transition hover:border-foreground hover:text-foreground">
                      Overview
                    </Link>
                    <Link href="/collections" className="border border-transparent px-3 py-2 transition hover:border-foreground hover:text-foreground">
                      Collections
                    </Link>
                    <ThemeToggle className="h-8 w-8 border border-border" />
                  </nav>
                </div>
              </div>
            </header>
            <main className="flex-1 pb-16">{children}</main>
            <footer className="border-t border-border bg-background">
              <div className="container flex h-12 items-center justify-between text-[0.65rem] uppercase tracking-[0.35em] text-muted-foreground">
                <span>CortexDB v0.1</span>
                <span>© {new Date().getFullYear()}</span>
              </div>
            </footer>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
