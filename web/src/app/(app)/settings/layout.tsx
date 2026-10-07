"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PageHeader } from "@/components/ui";

const TABS = [
  { href: "/settings/profile", label: "Profile" },
  { href: "/settings/security", label: "Security" },
  { href: "/settings/preferences", label: "Preferences" },
];

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <>
      <PageHeader title="Settings" />
      <nav className="mb-8 flex gap-2" aria-label="Settings sections">
        {TABS.map((t) => {
          const active = pathname === t.href;
          return (
            <Link key={t.href} href={t.href} aria-current={active ? "page" : undefined} className={`rounded-full border px-4 py-1.5 text-sm font-medium ${active ? "border-transparent bg-primary text-primary-fg" : "border-line-soft bg-surface text-muted hover:bg-sunken hover:text-fg"}`}>
              {t.label}
            </Link>
          );
        })}
      </nav>
      {children}
    </>
  );
}
