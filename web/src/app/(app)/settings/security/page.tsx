"use client";

import { useRouter } from "next/navigation";
import { Button, Card } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";

export default function SecuritySettings() {
  const { logout } = useAuth();
  const router = useRouter();
  return (
    <div className="max-w-xl space-y-4">
      <Card className="p-6">
        <h2 className="text-[17px] font-semibold">Sign out</h2>
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
      </Card>
      <Card className="p-6">
        <h2 className="text-[17px] font-semibold">Password</h2>
        <p className="mt-1 text-muted">Changing your password here isn’t available yet. It needs a backend endpoint that is planned for the security-hardening phase.</p>
      </Card>
    </div>
  );
}
