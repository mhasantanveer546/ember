/** Design tokens, the same dark palette as the web app (sampled from the product mockup). */
export const colors = {
  bg: "#0d1a27",
  sidebar: "#08111b",
  surface: "#10202e",
  sunken: "#152638",
  line: "#20364a",
  lineSoft: "#182b3c",
  fg: "#e8eef5",
  muted: "#8da0b4",
  faint: "#5c7087",
  primary: "#2f74b4",
  primaryFg: "#ffffff",
  primarySoft: "#0f2a47",
  web: "#5aa9ff",
  ember: "#ff7a2f",
  emberText: "#ff9a5c",
  glow: "rgba(255,122,47,0.28)",
  knowledge: "#0e2731",
  knowledgeLine: "#14413f",
  green: "#3fd6a0",
  ok: "#3fd6a0",
  warn: "#f2b45a",
  danger: "#ff8a7a",
  paper: "#f8f9f8",
  paperInk: "#1a2330",
} as const;

export const radius = { sm: 8, md: 12, lg: 16, xl: 22, pill: 999 } as const;
export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 } as const;
