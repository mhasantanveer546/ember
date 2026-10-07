import Link from "next/link";
import { useId } from "react";

/** The flame: orange gradient body with a dark hollow core. */
export function EmberMark({ className = "h-6 w-6", animate = false, glow = false }: { className?: string; animate?: boolean; glow?: boolean }) {
  const gid = `flame-${useId().replace(/:/g, "")}`;
  return (
    <svg
      viewBox="0 0 24 24"
      className={`${className} ${animate ? "flicker" : ""}`}
      style={{
        ...(animate ? { animation: "flicker 2.4s ease-in-out infinite", transformOrigin: "50% 90%" } : {}),
        ...(glow ? { filter: "drop-shadow(0 0 14px rgb(255 110 40 / 0.55))" } : {}),
      }}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={gid} x1="0.5" y1="0" x2="0.5" y2="1">
          <stop offset="0" stopColor="#ffb457" />
          <stop offset="0.55" stopColor="#ff7a2f" />
          <stop offset="1" stopColor="#f2411d" />
        </linearGradient>
      </defs>
      <path d="M12 2c.4 3 3.200 4.800 4.600 7.400 1 1.800 1.400 3.600 1.400 5.100a6 6 0 0 1-12 0c0-1.800.7-3.400 1.700-4.700.4 1.300 1.100 2.100 2 2.500C9 9.300 9.900 5 12 2Z" fill={`url(#${gid})`} />
      <path d="M12 13c1.600 1.500 2.500 2.600 2.500 3.900a2.500 2.500 0 0 1-5 0c0-1.300.9-2.400 2.500-3.900Z" fill="#4a1406" fillOpacity="0.8" />
    </svg>
  );
}

export function Logo({ href = "/dashboard", size = "md" }: { href?: string; size?: "md" | "lg" }) {
  return (
    <Link href={href} className="inline-flex items-center gap-2.5" aria-label="Ember home">
      <EmberMark className={size === "lg" ? "h-9 w-9" : "h-7 w-7"} />
      <span className={`font-semibold tracking-tight ${size === "lg" ? "text-3xl" : "text-[19px]"}`}>Ember</span>
    </Link>
  );
}
