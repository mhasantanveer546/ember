"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Logo } from "@/components/Logo";
import { useAuth } from "@/context/AuthContext";

/** A small, static picture of what Ember does: you remember a word, it finds the passage. */
function Demo() {
  return (
    <div aria-hidden="true" className="select-none">
      <div className="flex items-center gap-3 rounded-2xl border border-line bg-surface px-4 py-3 shadow-sm">
        <svg viewBox="0 0 24 24" className="h-5 w-5 text-faint" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"><path d="M11 5a6 6 0 1 0 0 12 6 6 0 0 0 0-12Zm9 15-4.2-4.2" /></svg>
        <span className="text-lg">congestion control</span>
      </div>

      <div className="mt-8 space-y-7">
        <div>
          <div className="mb-1.5 flex items-center gap-2 text-sm font-medium">
            <span className="inline-flex h-5 items-center rounded-[4px] bg-sunken px-1.5 text-[11px] font-semibold text-muted ring-1 ring-line-soft">.md</span>
            networking-week-9.md
          </div>
          <p className="passage">
            …TCP reacts to loss by shrinking its window. <mark className="hit">Congestion</mark> <mark className="hit">control</mark> is what keeps a
            sender from flooding the path, slow start doubles, then additive increase takes over…
          </p>
        </div>
        <div className="opacity-60">
          <div className="mb-1.5 flex items-center gap-2 text-sm font-medium">
            <span className="inline-flex h-5 items-center rounded-[4px] bg-sunken px-1.5 text-[11px] font-semibold text-muted ring-1 ring-line-soft">.pdf</span>
            transport-layer-slides.pdf
          </div>
          <p className="passage">
            …compare flow control with <mark className="hit">congestion</mark> <mark className="hit">control</mark>: one protects the receiver, the other protects the network…
          </p>
        </div>
      </div>
    </div>
  );
}

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [user, loading, router]);

  return (
    <div className="grid min-h-dvh lg:grid-cols-[1.1fr_1fr]">
      <section className="hidden flex-col justify-between bg-sunken px-14 py-12 lg:flex">
        <Logo href="/auth/login" />
        <div className="max-w-lg">
          <h2 className="display mb-10 text-[44px]">Find what you forgot you knew.</h2>
          <Demo />
        </div>
        <p className="text-sm text-muted">Your notes, papers and documents, searchable in one place.</p>
      </section>

      <section className="flex flex-col justify-center px-6 py-10 sm:px-12">
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
