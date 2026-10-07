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
      <nav className="mb-10 flex gap-6 border-b border-line" aria-label="Settings sections">
        {TABS.map((t) => {
          const active = pathname === t.href;
          return (
            <Link key={t.href} href={t.href} aria-current={active ? "page" : undefined} className={`-mb-px border-b-2 pb-3 text-[15px] ${active ? "border-ember font-semibold" : "border-transparent text-muted hover:text-fg"}`}>
              {t.label}
            </Link>
          );
        })}
      </nav>
      {children}
    </>
  );
}
