import { Skeleton } from "@/components/ui/skeleton";

export default function CoachingLoading() {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      {/* Sidebar skeleton */}
      <div className="hidden w-72 flex-col border-r border-border/50 p-4 md:flex">
        <Skeleton className="h-10 w-full rounded-lg" />
        <div className="mt-6 space-y-3">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-12 w-full rounded-md" />
          <Skeleton className="h-12 w-full rounded-md" />
          <Skeleton className="h-12 w-full rounded-md" />
        </div>
      </div>

      {/* Main chat workspace skeleton */}
      <div className="flex flex-1 flex-col">
        {/* Top bar */}
        <div className="flex h-14 items-center justify-between border-b border-border/50 px-6">
          <div className="flex items-center gap-3">
            <Skeleton className="h-8 w-8 rounded-full" />
            <Skeleton className="h-5 w-48" />
          </div>
          <Skeleton className="h-8 w-24 rounded-md" />
        </div>

        {/* Message stream area */}
        <div className="flex-1 space-y-6 overflow-y-auto p-6 md:p-8">
          {/* Assistant greeting bubble */}
          <div className="flex gap-4 max-w-2xl">
            <Skeleton className="h-9 w-9 shrink-0 rounded-full" />
            <div className="space-y-2 flex-1">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-20 w-full rounded-xl" />
            </div>
          </div>

          {/* User message bubble */}
          <div className="flex justify-end">
            <div className="space-y-2 max-w-lg">
              <Skeleton className="h-14 w-72 rounded-xl" />
            </div>
          </div>

          {/* Assistant response bubble */}
          <div className="flex gap-4 max-w-2xl">
            <Skeleton className="h-9 w-9 shrink-0 rounded-full" />
            <div className="space-y-2 flex-1">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-28 w-full rounded-xl" />
            </div>
          </div>
        </div>

        {/* Bottom input area */}
        <div className="border-t border-border/50 p-4">
          <div className="mx-auto max-w-3xl space-y-2">
            <Skeleton className="h-24 w-full rounded-xl" />
            <div className="flex justify-between items-center px-1">
              <Skeleton className="h-4 w-36" />
              <Skeleton className="h-9 w-20 rounded-md" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

