"use client";

import { Card } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";

export default function ProfileSettings() {
  const { user } = useAuth();
  if (!user) return null;
  return (
    <Card className="max-w-xl space-y-4">
      <div>
        <p className="text-sm text-muted">Email</p>
        <p className="font-medium">{user.email}</p>
      </div>
      <div>
        <p className="text-sm text-muted">Account ID</p>
        <p className="font-mono text-xs">{user.id}</p>
      </div>
      <p className="text-sm text-muted">Editing your email or display name isn&apos;t available yet.</p>
    </Card>
  );
}
