"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";

export default function SecuritySettings() {
  const { logout } = useAuth();
  const router = useRouter();
  return (
    <div className="max-w-lg divide-y divide-line-soft border-y border-line-soft">
      <section className="py-6">
        <h2 className="display text-lg">Sign out</h2>
        <p className="mt-1 text-muted">Ends this session and invalidates its sign-in token on the server.</p>
        <Button
          variant="secondary"
          className="mt-4"
          onClick={async () => {
            await logout();
            router.replace("/auth/login");
          }}
        >
          Sign out
        </Button>
      </section>
      <section className="py-6">
        <h2 className="display text-lg">Password</h2>
        <p className="mt-1 text-muted">Changing your password here isn’t available yet. It needs a backend endpoint that is planned for the security-hardening phase.</p>
      </section>
    </div>
  );
}
