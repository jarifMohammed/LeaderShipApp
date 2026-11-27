import { DashboardShell } from "@/features/dashboard/components/DashboardShell";
import { ManagerObservabilityDashboard } from "@/features/manager/components/ManagerObservabilityDashboard";

export const metadata = {
  title: "Platform Observability & Costs | LeaderCoach Manager",
};

export default function ManagerDashboardPage() {
  return (
    <DashboardShell title="Platform Observability & Unit Economics">
      <ManagerObservabilityDashboard />
    </DashboardShell>
  );
}

