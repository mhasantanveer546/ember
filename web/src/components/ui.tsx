"use client";

import Link from "next/link";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";
import { EmberMark } from "./Logo";
import { fileExtension } from "@/lib/format";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "md" | "sm";

const variants: Record<Variant, string> = {
  primary: "bg-ink text-ink-fg hover:opacity-90",
  secondary: "border border-line bg-transparent hover:bg-sunken",
  ghost: "text-muted hover:bg-sunken hover:text-fg",
  danger: "text-muted hover:bg-sunken hover:text-danger",
};
const sizes: Record<Size, string> = { md: "px-4 py-2 text-sm", sm: "px-2.5 py-1 text-[13px]" };

const base = "inline-flex items-center justify-center gap-2 rounded-lg font-medium disabled:cursor-not-allowed disabled:opacity-45";

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size }) {
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
        className={`w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm placeholder:text-faint hover:border-faint focus:border-ink ${className}`}
      />
      {hint && <p className="mt-1.5 text-xs text-muted">{hint}</p>}
    </div>
  );
}

export function Select({ label, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  return (
    <label className="block text-sm">
      <span className="mb-1.5 block font-medium">{label}</span>
      <select {...props} className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm hover:border-faint focus:border-ink">
        {children}
      </select>
    </label>
  );
}

/** Quiet container, used sparingly: only where a block needs to read as one object. */
export function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-2xl bg-surface p-6 ring-1 ring-line-soft ${className}`}>{children}</div>;
}

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: ReactNode; action?: ReactNode }) {
  return (
    <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        <h1 className="display text-[30px]">{title}</h1>
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

/** Loading placeholder shaped like the rows it stands in for. */
export function RowsSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div role="status" aria-label="Loading" className="divide-y divide-line-soft">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="space-y-2.5 py-5">
          <Skeleton className="h-3.5 w-1/4" />
          <Skeleton className="h-4 w-11/12" />
          <Skeleton className="h-4 w-3/5" />
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
      <EmberMark className="h-10 w-10" animate />
      {label}
    </div>
  );
}

export function ErrorNote({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-wrap items-center justify-between gap-3 border-l-2 border-danger bg-sunken px-4 py-3 text-sm">
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
    <div className="max-w-lg py-10">
      <EmberMark className="mb-4 h-8 w-8 opacity-70" />
      <h2 className="display text-xl">{title}</h2>
      {body && <p className="mt-2 text-[15px] leading-relaxed text-muted">{body}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

/** File-type tag: a small square label, like the tab on an index card. */
export function FileTag({ filename }: { filename: string }) {
  const ext = fileExtension(filename);
  return (
    <span className="inline-flex h-5 min-w-9 shrink-0 items-center justify-center rounded-[4px] bg-sunken px-1.5 text-[11px] font-semibold text-muted ring-1 ring-line-soft">
      .{ext || "file"}
    </span>
  );
}
