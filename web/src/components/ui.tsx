"use client";

import Link from "next/link";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";
import { EmberMark } from "./Logo";
import { Icon, type IconName } from "./Icon";
import { fileExtension } from "@/lib/format";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "md" | "sm";

const variants: Record<Variant, string> = {
  primary: "bg-primary text-primary-fg hover:brightness-110",
  secondary: "border border-line bg-surface hover:bg-sunken",
  ghost: "text-muted hover:bg-sunken hover:text-fg",
  danger: "text-muted hover:bg-sunken hover:text-danger",
};
const sizes: Record<Size, string> = { md: "px-4 py-2 text-sm", sm: "px-2.5 py-1 text-[13px]" };
const base = "inline-flex items-center justify-center gap-2 rounded-lg font-medium disabled:cursor-not-allowed disabled:opacity-45";

export function Button({ variant = "primary", size = "md", className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size }) {
  return <button {...props} className={`${base} ${sizes[size]} ${variants[variant]} ${className}`} />;
}

export function LinkButton({ href, children, variant = "primary", size = "md" }: { href: string; children: ReactNode; variant?: Variant; size?: Size }) {
  return (
    <Link href={href} className={`${base} ${sizes[size]} ${variants[variant]}`}>
      {children}
    </Link>
  );
}

export function Input({ label, hint, className = "", id, ...props }: InputHTMLAttributes<HTMLInputElement> & { label?: string; hint?: string }) {
  const inputId = id ?? props.name;
  return (
    <div className="text-sm">
      {label && (
        <label htmlFor={inputId} className="mb-1.5 block font-medium">
          {label}
        </label>
      )}
      <input
        id={inputId}
        {...props}
        className={`w-full rounded-lg border border-line bg-sunken px-3 py-2 text-sm placeholder:text-faint hover:border-faint focus:border-web ${className}`}
      />
      {hint && <p className="mt-1.5 text-xs text-muted">{hint}</p>}
    </div>
  );
}

export function Select({ label, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  return (
    <label className="block text-sm">
      <span className="mb-1.5 block font-medium">{label}</span>
      <select {...props} className="w-full rounded-lg border border-line bg-sunken px-3 py-2 text-sm hover:border-faint focus:border-web">
        {children}
      </select>
    </label>
  );
}

/** The standard container: a surface with a hairline border. */
export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-line-soft bg-surface ${className}`}>{children}</div>;
}

/** A card with a colored icon + title, like "Your Knowledge" in the product design. */
export function SectionCard({
  title,
  icon,
  tone = "default",
  count,
  children,
  className = "",
}: {
  title: string;
  icon: IconName;
  tone?: "default" | "knowledge";
  count?: number;
  children: ReactNode;
  className?: string;
}) {
  const knowledge = tone === "knowledge";
  return (
    <section className={`rounded-2xl border p-5 ${knowledge ? "border-knowledge-line bg-knowledge" : "border-line-soft bg-surface"} ${className}`}>
      <h2 className={`mb-3 flex items-center gap-2.5 text-[17px] font-semibold ${knowledge ? "text-green" : "text-web"}`}>
        <span className={`flex h-6 w-6 items-center justify-center rounded-md ${knowledge ? "bg-green/20" : "bg-web/20"}`}>
          <Icon name={icon} className="h-3.5 w-3.5" />
        </span>
        {title}
        {count !== undefined && <span className="text-[13px] font-normal text-muted tabular-nums">{count}</span>}
      </h2>
      {children}
    </section>
  );
}

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: ReactNode; action?: ReactNode }) {
  return (
    <header className="mb-7 flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        <h1 className="display text-[28px]">{title}</h1>
        {subtitle && <p className="mt-1.5 text-[15px] text-muted">{subtitle}</p>}
      </div>
      {action}
    </header>
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return <span role="status" aria-label={label} className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-line border-t-ember" />;
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-sunken ${className}`} />;
}

export function RowsSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div role="status" aria-label="Loading" className="divide-y divide-line-soft">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex gap-3 py-4">
          <Skeleton className="h-9 w-9 shrink-0" />
          <div className="flex-1 space-y-2.5">
            <Skeleton className="h-3.5 w-1/3" />
            <Skeleton className="h-3.5 w-5/6" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function LoadingBlock({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-12 text-sm text-muted">
      <Spinner label={label} /> {label}
    </div>
  );
}

export function FullScreenLoading({ label }: { label: string }) {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-3 text-sm text-muted" role="status">
      <EmberMark className="h-10 w-10" animate glow />
      {label}
    </div>
  );
}

export function ErrorNote({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-danger/40 bg-danger/10 px-4 py-3 text-sm">
      <span>{message}</span>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

export function EmptyState({ title, body, action }: { title: string; body?: string; action?: ReactNode }) {
  return (
    <div className="flex max-w-lg flex-col items-start py-8">
      <EmberMark className="mb-4 h-8 w-8 opacity-80" />
      <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
      {body && <p className="mt-2 text-[15px] leading-relaxed text-muted">{body}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

const TYPE_STYLE: Record<string, { bg: string; label: string }> = {
  pdf: { bg: "#e5484d", label: "PDF" },
  docx: { bg: "#2f74b4", label: "DOC" },
  md: { bg: "#6b52d6", label: "MD" },
  txt: { bg: "#5c7087", label: "TXT" },
};

/** Colored file-type tile (red PDF, blue Word, ...), as in the product design. */
export function FileTag({ filename, size = "md" }: { filename: string; size?: "md" | "lg" }) {
  const ext = fileExtension(filename);
  const t = TYPE_STYLE[ext] ?? { bg: "#5c7087", label: (ext || "FILE").slice(0, 4).toUpperCase() };
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-lg font-bold text-white ${size === "lg" ? "h-11 w-11 text-[11px]" : "h-8 w-8 text-[9.5px]"}`}
      style={{ backgroundColor: t.bg }}
      aria-label={`${t.label} file`}
    >
      {t.label}
    </span>
  );
}
