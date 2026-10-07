"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppShell } from "@/components/AppShell";
import { FullScreenLoading } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";

/** Everything inside (app)/ requires a signed-in user. */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/auth/login");
  }, [user, loading, router]);

  if (loading || !user) return <FullScreenLoading label="Opening Ember…" />;
  return <AppShell>{children}</AppShell>;
}
