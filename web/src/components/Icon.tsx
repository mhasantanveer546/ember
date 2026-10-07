/** One consistent icon set: 1.6 stroke, round caps, 24px grid. */
const PATHS = {
  home: "M4 10.5 12 4l8 6.5V19a1 1 0 0 1-1 1h-4.5v-5.5h-5V20H5a1 1 0 0 1-1-1z",
  search: "M11 5a6 6 0 1 0 0 12 6 6 0 0 0 0-12Zm9 15-4.2-4.2",
  file: "M7 3.5h6.5L19 9v10.5a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1v-15a1 1 0 0 1 1-1ZM13.500 3.500V9H19",
  folders: "M3.500 7a1 1 0 0 1 1-1H9l2 2h8.500a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1h-15a1 1 0 0 1-1-1z",
  sliders: "M4 7h8m4 0h4M4 17h3m4 0h9M14 7m-2 0a2 2 0 1 0 4 0 2 2 0 1 0-4 0M9 17m-2 0a2 2 0 1 0 4 0 2 2 0 1 0-4 0",
  chevron: "m7 10 5 5 5-5",
  up: "m7 14 5-5 5 5",
  down: "m7 10 5 5 5-5",
  menu: "M4 7h16M4 12h16M4 17h16",
  close: "M6 6l12 12M18 6 6 18",
  upload: "M12 16V5m0 0L8 9m4-4 4 4M5 19.500h14",
  back: "M15 6l-6 6 6 6",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, className = "h-[18px] w-[18px]" }: { name: IconName; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <path d={PATHS[name]} />
    </svg>
  );
}
