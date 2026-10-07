"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button, ErrorNote, Input } from "@/components/ui";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email.trim(), password);
      router.replace("/dashboard");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <h1 className="display text-[28px]">Sign in</h1>
      {error && <ErrorNote message={error} />}
      <Input label="Email" name="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
      <Input label="Password" name="password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
      <Button type="submit" disabled={busy} className="w-full">
        {busy ? "Signing in…" : "Sign in"}
      </Button>
      <div className="flex justify-between text-sm text-muted">
        <Link href="/auth/forgot-password" className="hover:text-fg">Forgot password?</Link>
        <Link href="/auth/register" className="font-medium text-fg underline decoration-ember decoration-2 underline-offset-4">Create an account</Link>
      </div>
    </form>
  );
}
