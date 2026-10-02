"use client";

import { useRouter } from "next/navigation";
import { Button, Card } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";

export default function SecuritySettings() {
  const { logout } = useAuth();
  const router = useRouter();
  return (
    <div className="max-w-xl space-y-4">
      <Card>
        <h2 className="font-serif text-lg font-semibold">Session</h2>
        <p className="mt-1 text-sm text-muted">Signing out ends this session and invalidates its token on the server.</p>
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
      </Card>
      <Card>
        <h2 className="font-serif text-lg font-semibold">Password</h2>
        <p className="mt-1 text-sm text-muted">Changing your password from here isn&apos;t available yet. It needs a backend endpoint that is planned for the security-hardening phase.</p>
      </Card>
    </div>
  );
}
