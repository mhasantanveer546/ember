"use client";

import { Card } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";

export default function ProfileSettings() {
  const { user } = useAuth();
  if (!user) return null;
  return (
    <Card className="max-w-xl p-6">
      <div className="mb-6 flex items-center gap-4">
        <span className="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-[#ffb08a] to-[#ff6b4a] text-xl font-semibold text-[#3a1308]">{user.email[0].toUpperCase()}</span>
        <div className="min-w-0">
          <p className="truncate text-lg font-semibold">{user.email}</p>
          <p className="text-sm text-muted">Signed in</p>
        </div>
      </div>
      <dl className="divide-y divide-line-soft border-y border-line-soft">
        <div className="py-3.5"><dt className="text-sm text-muted">Email</dt><dd className="mt-0.5 font-medium">{user.email}</dd></div>
        <div className="py-3.5"><dt className="text-sm text-muted">Account ID</dt><dd className="mt-0.5 break-all text-sm tabular-nums">{user.id}</dd></div>
      </dl>
      <p className="mt-4 text-sm text-muted">Changing your email isn’t available yet.</p>
    </Card>
  );
}
