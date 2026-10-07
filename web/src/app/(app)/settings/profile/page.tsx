"use client";

import { useAuth } from "@/context/AuthContext";

export default function ProfileSettings() {
  const { user } = useAuth();
  if (!user) return null;
  return (
    <div className="max-w-lg">
      <dl className="divide-y divide-line-soft border-y border-line-soft">
        <div className="py-4">
          <dt className="text-sm text-muted">Email</dt>
          <dd className="mt-0.5 font-medium">{user.email}</dd>
        </div>
        <div className="py-4">
          <dt className="text-sm text-muted">Account ID</dt>
          <dd className="mt-0.5 break-all text-sm tabular-nums">{user.id}</dd>
        </div>
      </dl>
      <p className="mt-4 text-sm text-muted">Changing your email isn’t available yet.</p>
    </div>
  );
}
