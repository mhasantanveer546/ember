"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { HeroArt } from "@/components/HeroArt";
import { EmberMark, Logo } from "@/components/Logo";
import { useAuth } from "@/context/AuthContext";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [user, loading, router]);

  return (
    <div className="grid min-h-dvh lg:grid-cols-[1.15fr_1fr]">
      <section className="relative isolate hidden flex-col justify-between overflow-hidden px-14 py-12 text-white lg:flex">
        <HeroArt className="absolute inset-0 -z-10 h-full w-full" />
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-black/30 via-transparent to-black/40" />
        <Logo href="/auth/login" />
        <div className="max-w-md pb-6 text-center mx-auto">
          <EmberMark className="mx-auto h-14 w-14" glow />
          <h2 className="mt-4 text-6xl font-bold tracking-tight">Ember</h2>
          <p className="mt-3 text-xl text-white/80">Find what you forgot you knew.</p>
        </div>
        <p className="text-sm text-white/60">Your notes, papers and documents, searchable in one place.</p>
      </section>

      <section className="flex flex-col justify-center bg-bg px-6 py-10 sm:px-12">
        <div className="mx-auto w-full max-w-sm">
          <div className="mb-10 lg:hidden">
            <Logo href="/auth/login" size="lg" />
            <p className="mt-3 text-muted">Find what you forgot you knew.</p>
          </div>
          {children}
        </div>
      </section>
    </div>
  );
}
