import Link from "next/link";
import { EmberMark } from "@/components/Logo";

export default function NotFound() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-6 text-center">
      <EmberMark className="h-12 w-12 opacity-60" />
      <h1 className="display mt-6 text-4xl">This page has gone out.</h1>
      <p className="mt-3 max-w-sm text-muted">The address may be wrong, or the page was removed. Your documents are safe.</p>
      <Link href="/dashboard" className="mt-8 rounded-lg bg-ink px-5 py-2.5 text-sm font-medium text-ink-fg hover:opacity-90">
        Go to Home
      </Link>
    </div>
  );
}
