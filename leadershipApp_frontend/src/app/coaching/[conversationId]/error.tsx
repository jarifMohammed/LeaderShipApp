"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, MessageSquarePlus, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function CoachingError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Coaching session error boundary caught:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600 dark:bg-red-950/50 dark:text-red-400">
        <AlertTriangle className="h-7 w-7" aria-hidden="true" />
      </div>

      <h2 className="mt-4 text-xl font-semibold tracking-tight text-foreground">
        Unable to Load Coaching Session
      </h2>

      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        {error.message ||
          "An unexpected error occurred while loading this leadership coaching conversation. Your past messages remain safely stored."}
      </p>

      {error.digest && (
        <p className="mt-1 font-mono text-xs text-muted-foreground/75">
          Error Digest: {error.digest}
        </p>
      )}

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <Button onClick={() => reset()} variant="outline" className="gap-2">
          <RotateCcw className="h-4 w-4" />
          Try Again
        </Button>

        <Button asChild className="gap-2">
          <Link href="/coaching/new">
            <MessageSquarePlus className="h-4 w-4" />
            Start New Session
          </Link>
        </Button>
      </div>
    </div>
  );
}

