import Link from "next/link";

export function EmberMark({ className = "h-6 w-6", animate = false }: { className?: string; animate?: boolean }) {
  return (
    <svg viewBox="0 0 24 24" className={`${className} ${animate ? "flicker" : ""}`} style={animate ? { animation: "flicker 2.4s ease-in-out infinite", transformOrigin: "50% 90%" } : undefined} aria-hidden="true">
      <path d="M12 2.200c.9 3.900 6 6.300 6 11.800a6 6 0 0 1-12 0c0-2.600 1.200-4.300 2.600-5.600.3 1.800 1.300 2.600 2.300 2.900C10.200 8.700 10.600 5.200 12 2.200Z" fill="var(--ember)" />
      <path d="M12 13c1.600 1.600 2.600 2.700 2.600 4.100a2.600 2.600 0 0 1-5.200 0c0-1.400 1-2.500 2.600-4.100Z" fill="var(--glow)" />
    </svg>
  );
}

export function Logo({ href = "/dashboard", size = "md" }: { href?: string; size?: "md" | "lg" }) {
  return (
    <Link href={href} className="inline-flex items-center gap-2" aria-label="Ember home">
      <EmberMark className={size === "lg" ? "h-9 w-9" : "h-6 w-6"} />
      <span className={`display ${size === "lg" ? "text-4xl" : "text-[22px]"}`}>Ember</span>
    </Link>
  );
}
