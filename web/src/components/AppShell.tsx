"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Icon, type IconName } from "./Icon";
import { Logo } from "./Logo";
import { WorkspaceSelector } from "./WorkspaceSelector";

const NAV: { href: string; label: string; icon: IconName }[] = [
  { href: "/dashboard", label: "Home", icon: "home" },
  { href: "/search", label: "Search", icon: "search" },
  { href: "/documents", label: "Knowledge", icon: "knowledge" },
  { href: "/workspaces", label: "Workspaces", icon: "layers" },
  { href: "/history", label: "History", icon: "clock" },
];

const MOBILE_TABS: { href: string; label: string; icon: IconName }[] = [
  { href: "/dashboard", label: "Home", icon: "home" },
  { href: "/search", label: "Search", icon: "search" },
  { href: "/documents", label: "Knowledge", icon: "knowledge" },
  { href: "/settings", label: "Profile", icon: "user" },
];

const isActive = (pathname: string, href: string) => pathname === href || pathname.startsWith(`${href}/`);

function NavLink({ href, label, icon, pathname }: { href: string; label: string; icon: IconName; pathname: string }) {
  const active = isActive(pathname, href);
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-[14px] ${active ? "bg-sunken font-semibold text-fg" : "text-muted hover:bg-sunken/60 hover:text-fg"}`}
    >
      <Icon name={icon} className={`h-[18px] w-[18px] ${active ? "text-web" : ""}`} />
      {label}
    </Link>
  );
}

function AvatarMenu() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", esc);
    };
  }, [open]);

  if (!user) return null;
  const item = "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm hover:bg-sunken";
  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        title={user.email}
        className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-[#ffb08a] to-[#ff6b4a] text-sm font-semibold text-[#3a1308]"
      >
        {user.email[0].toUpperCase()}
      </button>
      {open && (
        <div role="menu" className="absolute right-0 z-40 mt-2 w-60 rounded-xl border border-line bg-surface p-1.5 shadow-pop">
          <p className="truncate px-3 py-2 text-xs text-muted">{user.email}</p>
          <Link href="/workspaces" role="menuitem" onClick={() => setOpen(false)} className={item}><Icon name="layers" className="h-4 w-4 text-muted" /> Workspaces</Link>
          <Link href="/history" role="menuitem" onClick={() => setOpen(false)} className={item}><Icon name="clock" className="h-4 w-4 text-muted" /> History</Link>
          <Link href="/settings" role="menuitem" onClick={() => setOpen(false)} className={item}><Icon name="gear" className="h-4 w-4 text-muted" /> Settings</Link>
          <button
            role="menuitem"
            onClick={async () => {
              setOpen(false);
              await logout();
              router.replace("/auth/login");
            }}
            className={`${item} border-t border-line-soft`}
          >
            <Icon name="logout" className="h-4 w-4 text-muted" /> Sign out
          </button>
        </div>
      )}
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const home = pathname === "/dashboard";
  const reader = /^\/documents\/[^/]+$/.test(pathname);

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
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-fg">
        Skip to content
      </a>

      <aside className="sticky top-0 hidden h-dvh w-[224px] shrink-0 flex-col border-r border-line-soft bg-sidebar px-3.5 py-5 md:flex">
        <div className="px-2"><Logo /></div>
        <nav aria-label="Main" className="mt-8 flex flex-col gap-1">
          {NAV.map((n) => <NavLink key={n.href} {...n} pathname={pathname} />)}
        </nav>
        <div className="mt-auto">
          <NavLink href="/settings" label="Settings" icon="gear" pathname={pathname} />
        </div>
      </aside>

      <div className="relative flex min-w-0 flex-1 flex-col">
        <header className={`z-30 flex h-16 items-center gap-3 px-4 md:px-8 ${home ? "absolute inset-x-0 top-0" : "sticky top-0 border-b border-line-soft bg-bg/85 backdrop-blur"}`}>
          <div className="md:hidden"><Logo /></div>
          <div className="max-w-60 min-w-0"><WorkspaceSelector /></div>
          <div className="ml-auto flex items-center gap-3">
            <Link href="/search" className="rounded-full p-2 text-muted hover:bg-sunken hover:text-fg md:hidden" aria-label="Search"><Icon name="search" /></Link>
            <AvatarMenu />
          </div>
        </header>

        <main id="main" className={home ? "flex-1 pb-20 md:pb-0" : `mx-auto w-full flex-1 px-4 pb-28 pt-6 md:px-8 md:pb-14 md:pt-8 ${reader ? "max-w-none" : "max-w-[1180px]"}`}>
          {children}
        </main>
      </div>

      <nav aria-label="Mobile" className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-4 border-t border-line-soft bg-sidebar/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden">
        {MOBILE_TABS.map((t) => {
          const active = isActive(pathname, t.href);
          return (
            <Link key={t.href} href={t.href} aria-current={active ? "page" : undefined} className={`flex flex-col items-center gap-1 py-2.5 text-[11px] ${active ? "font-semibold text-web" : "text-muted"}`}>
              <Icon name={t.icon} className="h-5 w-5" />
              {t.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
