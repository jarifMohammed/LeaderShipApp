import { CoachWorkspacePage } from "@/features/coach-workspace/components/CoachWorkspacePage";

export default async function UserSupervisionPage({
  params,
}: {
  params: Promise<{ userId: string }>;
}) {
  const { userId } = await params;
  return <CoachWorkspacePage userId={userId} />;
}

