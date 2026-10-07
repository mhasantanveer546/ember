"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Icon, type IconName } from "./Icon";
import { Logo } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";
import { WorkspaceSelector } from "./WorkspaceSelector";

const NAV: { href: string; label: string; icon: IconName }[] = [
  { href: "/dashboard", label: "Home", icon: "home" },
  { href: "/search", label: "Search", icon: "search" },
  { href: "/documents", label: "Documents", icon: "file" },
  { href: "/workspaces", label: "Workspaces", icon: "folders" },
  { href: "/settings", label: "Settings", icon: "sliders" },
];

function SidebarBody({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  return (
    <div className="flex h-full flex-col gap-6">
      <Logo />
      <WorkspaceSelector />
      <nav aria-label="Main" className="flex flex-col gap-0.5">
        {NAV.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={`relative flex items-center gap-3 rounded-lg px-3 py-2 text-[15px] ${
                active ? "bg-sunken font-semibold text-fg" : "text-muted hover:bg-sunken/70 hover:text-fg"
              }`}
            >
              {active && <span className="absolute -left-4 top-2 bottom-2 w-[3px] rounded-r bg-ember" />}
              <Icon name={item.icon} className={`h-[18px] w-[18px] ${active ? "text-ember-text" : ""}`} />
              {item.label}
              {item.href === "/search" && <kbd className="ml-auto rounded border border-line px-1.5 text-[11px] text-faint">/</kbd>}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto space-y-4">
        <ThemeToggle />
        {user && (
          <div className="flex items-center gap-3 border-t border-line-soft pt-4">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] bg-ink text-sm font-semibold text-ink-fg">{user.email[0].toUpperCase()}</span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-[13px] font-medium" title={user.email}>{user.email}</p>
              <button
                onClick={async () => {
                  await logout();
                  router.replace("/auth/login");
                }}
                className="text-[13px] text-muted hover:text-fg"
              >
                Sign out
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [drawer, setDrawer] = useState(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- close the mobile drawer after navigation
    setDrawer(false);
  }, [pathname]);

  // "/" jumps to search from anywhere (focuses the box if this page has one).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "/" || e.metaKey || e.ctrlKey || e.altKey) return;
      const t = e.target as HTMLElement | null;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable)) return;
      e.preventDefault();
      const box = document.querySelector<HTMLInputElement>("[data-search-input]");
      if (box) box.focus();
      else router.push("/search");
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [router]);

  return (
    <div className="flex min-h-dvh">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-ink focus:px-4 focus:py-2 focus:text-ink-fg">
        Skip to content
      </a>

      <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 border-r border-line-soft px-6 py-6 md:block">
        <SidebarBody />
      </aside>

      {drawer && (
        <div className="fixed inset-0 z-40 md:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <button className="absolute inset-0 bg-black/40" onClick={() => setDrawer(false)} aria-label="Close menu" />
          <aside className="relative h-full w-72 bg-bg px-6 py-6 shadow-pop">
            <SidebarBody onNavigate={() => setDrawer(false)} />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-line-soft bg-bg/90 px-4 backdrop-blur md:hidden">
          <button onClick={() => setDrawer(true)} className="-ml-1 rounded-lg p-2 text-muted hover:bg-sunken" aria-label="Open menu">
            <Icon name="menu" />
          </button>
          <Logo />
          <Link href="/search" className="ml-auto rounded-lg p-2 text-muted hover:bg-sunken" aria-label="Search">
            <Icon name="search" />
          </Link>
        </header>
        <main id="main" className="mx-auto w-full max-w-4xl flex-1 px-5 py-8 md:px-12 md:py-14">
          {children}
        </main>
      </div>
    </div>
  );
}
