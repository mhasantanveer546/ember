/** One consistent icon set: 1.6 stroke, round caps, 24px grid. */
const PATHS = {
  home: "M4 10.500 12 4l8 6.500V19a1 1 0 0 1-1 1h-4.500v-5.500h-5V20H5a1 1 0 0 1-1-1z",
  search: "M11 5a6 6 0 1 0 0 12 6 6 0 0 0 0-12Zm9 15-4.200-4.200",
  knowledge: "M7 3.500h6.500L19 9v10.500a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1v-15a1 1 0 0 1 1-1ZM13.500 3.500V9H19M9 13h6M9 16.500h4",
  folders: "M3.500 7a1 1 0 0 1 1-1H9l2 2h8.500a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1h-15a1 1 0 0 1-1-1z",
  clock: "M12 4a8 8 0 1 0 0 16 8 8 0 0 0 0-16ZM12 8v4.200l2.800 1.800",
  gear: "M12 8.500a3.500 3.500 0 1 0 0 7 3.500 3.500 0 0 0 0-7ZM12 3v2.200M12 18.800V21M3 12h2.200M18.800 12H21M5.600 5.600l1.600 1.600M16.800 16.800l1.600 1.600M5.600 18.400l1.600-1.600M16.800 7.200l1.600-1.600",
  chevron: "m7 10 5 5 5-5",
  up: "m7 14 5-5 5 5",
  down: "m7 10 5 5 5-5",
  menu: "M4 7h16M4 12h16M4 17h16",
  close: "M6 6l12 12M18 6 6 18",
  upload: "M12 16V5m0 0L8 9m4-4 4 4M5 19.500h14",
  back: "M15 6l-6 6 6 6",
  plus: "M12 5v14M5 12h14",
  minus: "M5 12h14",
  user: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM5 20a7 7 0 0 1 14 0",
  logout: "M10 5H6a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h4M15 8l4 4-4 4M19 12H9",
  layers: "m12 4 8 4.500-8 4.500-8-4.500L12 4ZM4 12.500l8 4.500 8-4.500M4 16.500l8 4.500 8-4.500",
  spark: "M12 4v4M12 16v4M4 12h4M16 12h4M7 7l2 2M15 15l2 2M17 7l-2 2M9 15l-2 2",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, className = "h-[18px] w-[18px]" }: { name: IconName; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <path d={PATHS[name]} />
    </svg>
  );
}
