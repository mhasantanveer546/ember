import Link from "next/link";

export function Logo({ href = "/dashboard", size = "md" }: { href?: string; size?: "md" | "lg" }) {
  return (
    <Link href={href} className="flex items-center gap-2" aria-label="Ember home">
      <svg viewBox="0 0 24 24" className={size === "lg" ? "h-8 w-8" : "h-6 w-6"} aria-hidden="true">
        <path d="M12 2c1 4-3 5-3 9a3 3 0 0 0 6 0c0-1.5-.6-2.4-1.2-3.4C15.6 9 19 11 19 15a7 7 0 0 1-14 0c0-5 5-6.500 7-13z" fill="var(--accent)" />
      </svg>
      <span className={`font-serif font-semibold tracking-tight ${size === "lg" ? "text-3xl" : "text-xl"}`}>Ember</span>
    </Link>
  );
}
