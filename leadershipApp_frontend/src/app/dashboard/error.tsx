"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertOctagon, Home, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Dashboard error boundary caught:", error);
  }, [error]);

  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center p-8 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600 dark:bg-red-950/50 dark:text-red-400">
        <AlertOctagon className="h-7 w-7" aria-hidden="true" />
      </div>

      <h2 className="mt-4 text-2xl font-bold tracking-tight text-foreground">
        Dashboard View Unavailable
      </h2>

      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        {error.message ||
          "An error interrupted loading the dashboard view. You can reload this section or return to the main portal."}
      </p>

      {error.digest && (
        <p className="mt-1 font-mono text-xs text-muted-foreground/70">
          Digest: {error.digest}
        </p>
      )}

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <Button onClick={() => reset()} variant="outline" className="gap-2">
          <RotateCcw className="h-4 w-4" />
          Reload Section
        </Button>

        <Button asChild className="gap-2">
          <Link href="/dashboard">
            <Home className="h-4 w-4" />
            Return to Dashboard Home
          </Link>
        </Button>
      </div>
    </div>
  );
}

