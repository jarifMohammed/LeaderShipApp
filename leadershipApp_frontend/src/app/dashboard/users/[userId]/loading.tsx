import { Skeleton } from "@/components/ui/skeleton";

export default function UserSupervisionLoading() {
  return (
    <div className="space-y-6 p-6 max-w-7xl mx-auto">
      {/* Client header banner skeleton */}
      <div className="flex flex-col gap-4 rounded-xl border border-border/50 bg-card p-6 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <Skeleton className="h-16 w-16 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-64" />
          </div>
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-9 w-28 rounded-md" />
          <Skeleton className="h-9 w-32 rounded-md" />
        </div>
      </div>

      {/* Tabs navigation skeleton */}
      <div className="flex gap-2 border-b border-border/50 pb-2">
        <Skeleton className="h-9 w-32 rounded-md" />
        <Skeleton className="h-9 w-36 rounded-md" />
        <Skeleton className="h-9 w-36 rounded-md" />
        <Skeleton className="h-9 w-32 rounded-md" />
      </div>

      {/* Tab content grid skeleton */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* Main 2-column cards */}
        <div className="space-y-6 md:col-span-2">
          <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-24 w-full" />
          </div>
          <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
            <Skeleton className="h-5 w-48" />
            <div className="grid grid-cols-2 gap-4">
              <Skeleton className="h-28 w-full rounded-lg" />
              <Skeleton className="h-28 w-full rounded-lg" />
            </div>
          </div>
        </div>

        {/* Right sidebar column */}
        <div className="space-y-6">
          <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-36 w-full" />
          </div>
        </div>
      </div>
    </div>
  );
}

