# Ember web design system

Based on the product mockup (`Ember_Images.png`): a dark, teal-tinted navy interface with a flame brand mark, a sunset-mountain home screen, steel-blue actions and a green "Your Knowledge" section.

## Tokens (`web/src/app/globals.css`)
- **Dark (default):** bg `#0d1a27`, sidebar `#08111b`, surface `#10202e`, line `#20364a`, primary `#2f74b4`, ember `#ff7a2f`, knowledge card `#0e2731` / `#14413f`, green `#3fd6a0`, web-blue `#5aa9ff`.
- **Light:** same structure (bg `#f2f5f9`, white surfaces, primary `#2563b0`); the hero artwork stays dark in both themes.
- Components reference tokens only (`bg-surface`, `text-muted`, `bg-primary`, `text-web`, `bg-knowledge`, ...), so a re-skin is a change to the variables.

## Type
Inter (variable, self-hosted via `@fontsource-variable/inter`). Headings weight 600-700, tight tracking.

## Signature elements
- **Flame logo** (`EmberMark`): orange gradient with a dark core; unique gradient id per instance (gradients inside `display:none` SVGs do not resolve).
- **Home hero:** generated sunset mountains (`HeroArt`), pill search, quick-action pills, Add / Search / Recall strip.
- **Matches kindle:** matched words glow once when results appear (`mark.hit`); on white "paper" previews they use a light orange mark.
- **Search page:** filter pills, green "Your Knowledge" section card, right-hand preview panel (white page + "Open document").
- **Reader:** match list on the left (selected match has a blue border), white page, text-size control (70-160%).
- **Navigation:** Home, Search, Knowledge (documents), Workspaces, History; Settings pinned at the bottom. Mobile uses a bottom tab bar.

## Not built yet (shown in the mockup, no backend support)
Web search and results, Browser, Bookmarks, "Ask Ember" AI chat, PDF page thumbnails. These belong to later roadmap versions (web search, AI/RAG) and are intentionally not faked in the UI.
