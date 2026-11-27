"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertCircle, ArrowLeft, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function UserSupervisionError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Coach Command Center error boundary caught:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-amber-100 text-amber-600 dark:bg-amber-950/50 dark:text-amber-400">
        <AlertCircle className="h-7 w-7" aria-hidden="true" />
      </div>

      <h2 className="mt-4 text-xl font-semibold tracking-tight text-foreground">
        Unable to Load Client Supervision Dossier
      </h2>

      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        {error.message ||
          "Could not retrieve the 360° executive memory profile or session history for this client."}
      </p>

      {error.digest && (
        <p className="mt-1 font-mono text-xs text-muted-foreground/75">
          Error Digest: {error.digest}
        </p>
      )}

      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <Button onClick={() => reset()} variant="outline" className="gap-2">
          <RotateCcw className="h-4 w-4" />
          Retry Dossier Load
        </Button>

        <Button asChild variant="secondary" className="gap-2">
          <Link href="/dashboard/users">
            <ArrowLeft className="h-4 w-4" />
            Back to Client Directory
          </Link>
        </Button>
      </div>
    </div>
  );
}

