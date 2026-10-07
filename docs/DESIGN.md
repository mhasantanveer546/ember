# Ember web design system

## Idea
Interface chrome is sans-serif; anything that is *your own knowledge* (search passages, document text) is a reading serif.
Matched words "kindle" like embers. That is the one memorable element; everything else stays quiet.

## Tokens (`web/src/app/globals.css`)
- **Light, "linen":** bg `#f1f0eb`, ink `#1f1e1b`, hairlines `#d6d3c9`.
- **Dark, "char":** bg `#161513`, ink `#edeae2`, ember `#ff9b3d`.
- **One accent, ember** (`--ember`), used only for: matched words, the active-nav marker, the logo, progress. Primary buttons are ink, not orange.
- Text on light backgrounds uses `--ember-text` (#a54d08) so it passes contrast.

## Type
- UI and headings: **Bricolage Grotesque** (variable), weights 400-600, tight tracking on headings (`.display`).
- Content: **Source Serif 4** (variable) via `.passage`, 17-18px, 1.7-1.8 line height, 68ch measure.
- Both are self-hosted through `@fontsource-variable/*` (no Google Fonts request, works offline).

## Patterns
- Lists with hairline dividers instead of card grids. `Panel` exists but is rarely used.
- File type shown as a small square tag (`.md`), status as dot + word (not pills).
- Skeleton rows while loading; empty states say what to do next.
- Numbered steps only where the content is a real sequence (first-run onboarding).
- Motion: matches kindle once when results appear; the logo flickers only on the full-screen loader; both respect `prefers-reduced-motion`.
- Keyboard: `/` jumps to search from anywhere; visible ember focus ring; skip-to-content link.

## Changing the look
Edit the CSS variables in `globals.css`; components only reference tokens (`bg-sunken`, `text-muted`, `bg-ink`, ...).
