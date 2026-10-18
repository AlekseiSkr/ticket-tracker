---
name: "Ticket Tracker"
description: "The admin's design system: benrey.io's language applied to an Operate-mode Django admin (Unfold). Recorded from the shipped build on 2026-10-15."
colors:
  lime-signal: "#C3FF00"
  lime-ink: "#CBFB2E"
  lime-hover: "#DBFF66"
  ink: "#060606"
  panel: "#0C0C0C"
  void: "#000000"
  heading: "#EBECEB"
  body: "#B8B9B6"
  muted: "#B1B2B0"
  subtle: "#A3A4A0"
  hairline: "#232523"
  divider: "#3C3C3C"
  edge: "#626561"
  white: "#FFFFFF"
typography:
  page-title:
    fontFamily: "Archivo"
    fontSize: "1.25rem"
    fontWeight: 800
    lineHeight: "1.75rem"
    fontVariation: "'wdth' 125"
  dashboard-title:
    fontFamily: "Archivo"
    fontSize: "2rem"
    fontWeight: 800
    lineHeight: 1.25
    fontVariation: "'wdth' 125"
  lead:
    fontFamily: "Geist"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  body:
    fontFamily: "Geist"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.43
  label:
    fontFamily: "Geist Mono"
    fontSize: "0.875rem"
    fontWeight: 500
    letterSpacing: "-0.01em"
  caption:
    fontFamily: "Geist Mono"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: "1.25rem"
    letterSpacing: "0.02em"
rounded:
  default: "8px"
spacing:
  sidebar-tick: "6px"
  lit-line: "10px"
components:
  button-primary:
    backgroundColor: "{colors.lime-signal}"
    textColor: "{colors.panel}"
    typography: "{typography.label}"
    rounded: "{rounded.default}"
  button-primary-hover:
    backgroundColor: "{colors.lime-hover}"
  button-on-lime:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.lime-ink}"
    rounded: "{rounded.default}"
  input:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.heading}"
    rounded: "{rounded.default}"
  nav-item-active:
    textColor: "{colors.lime-ink}"
---

# Design System: Ticket Tracker

## Overview

**"Mission Control at Night", at work.**

benrey.io's language — a near-black console lit by one acid lime — applied to a working admin. On this Operate surface the world lends only four things:
- **type:** wide oblique for page titles, Geist for UI, Geist Mono for labels and data;
- **palette:** ink black plus one lime;
- **density:** Unfold's standard admin density;
- **one signature move:** the lit line.

Navigation, tables, forms and controls stay Django's and Unfold's own, so an agent knows where everything is before noticing the style.

Source capture: `C:\Users\Aleksei\Software\Projects\design-lab\benrey.io\DESIGN.md` (measured 2026-10-15). Wiring: [features/design-language.md](features/design-language.md).

## Colors

### Primary
- **Lime Signal** (#C3FF00): fills — primary buttons, the add (+) button, checked switches and checkboxes, the selection action bar.
- **Lime Ink** (#CBFB2E): lime as light and text — the active nav item, form section captions, the lit line, text selection, the caret.
- **Lime Hover** (#DBFF66): the hover fill of primary buttons.

### Neutral
- **Ink** (#060606): the page.
- **Panel** (#0C0C0C): the second neutral layer (sidebar, inputs), and dark text on lime.
- **Void** (#000000): container interiors inside the conic edge.
- **Heading** (#EBECEB): titles.
- **Body** (#B8B9B6): default text.
- **Muted** (#B1B2B0): table headers and parent breadcrumbs.
- **Subtle** (#A3A4A0): secondary text and placeholders. It's lighter than the source's #868783 so it holds 4.5:1 on Unfold's raised greys.
- **Hairline / Divider / Edge** (#232523 / #3C3C3C / #626561): rules, borders, input hover.
- **White** (#FFFFFF): focus rings and header navigation text.

### Status
Unfold's red, amber, green and blue keep their meaning:
- red: destructive or error;
- amber: warning;
- green: success;
- blue: info (the "Local" environment badge).

### Named Rules
- **One Lime Rule:** lime marks the primary action, the current selection or state, and the signature line. Nothing decorative.
- **Dark text on lime, always:** #0C0C0C. Unfold ships `text-white` on lime fills, and `theme.css` overrides it.

## Typography

- **Display:** Archivo, variable, `font-stretch: 125%`, weight 800, italic. It stands in for the source's licensed Base Neue Wide.
- **UI:** Geist.
- **Labels and data:** Geist Mono.

All three are self-hosted OFL fonts in `core/static/core/fonts/`.

### Hierarchy
- **Dashboard title** (800, 2rem / 1.25): the greeting, and the error-page headline.
- **Page title** (800, 1.25rem / 1.75rem): the current page, the last breadcrumb segment.
- **Lead** (Geist 400, 1rem / 1.5): copy on standalone pages (the error pages).
- **Body** (Geist 400, 0.875rem): Unfold's default.
- **Label** (Geist Mono 500, 0.875rem, -0.01em): field labels, buttons (uppercase), table headers (0.75rem uppercase).
- **Caption** (Geist Mono 400, 0.75rem / 1.25rem, uppercase, lime, 8 px square bullet): form section headings. These are the headings themselves, never a kicker above one.

### Named Rules
- **Display for titles only.** Never on labels, buttons or data.
- **Numbers are tabular** in tables and timestamps.

## Layout

Unfold's shell, unchanged:
- **Sidebar:** permission-aware, with search (⌘K also searches navigation).
- **Header:** breadcrumb, environment badge, history and add.
- **Content:** a centred container, and the sticky submit row on forms.

The dashboard adds a greeting with today's date above Unfold's app list and recent actions.

## Elevation & Depth

Flat and tonal, with no drop shadows.

### Shadow Vocabulary
- **Lit line** (`box-shadow: 0 0 18px 0 #CBFB2E`): the signature move, and nowhere else. It marks the active sidebar item (10 px line), the dashboard rule (110 px) and the error page.

### Named Rules
- **Edge, not shadow.** Top-level form fieldsets and the recent-actions panel get the source's 1 px conic-gradient edge (`#666 → #222`, from 135°) over a black interior. Never nested inside another edged container.

## Shapes

8 px corners everywhere (`UNFOLD["BORDER_RADIUS"]`). Pills are only Unfold's own badges and switches.

## Components

### Buttons
- **Primary:** Lime Signal fill, #0C0C0C uppercase Geist Mono 600.
- **Hover:** #DBFF66, 120 ms.
- **Active:** `scale(.98)`.
- **Focus:** 2 px white outline, 3 px offset.
- **Disabled:** 45 % opacity, `not-allowed` cursor.
- **On a lime surface** (action bar "Run"): Panel fill with Lime Ink text.

### Inputs / Fields
- **Style:** Panel background, Divider border (Edge on hover), lime caret.
- **Focus:** 2 px white outline.
- **Placeholder:** Subtle.
- **Switches and checkboxes:** lime when on, with a dark thumb or tick. They keep a focus ring; Unfold's `focus:outline-none` is overridden.

### Navigation
The signature move: every sidebar item has a 6 px divider-grey tick, like the source's timeline.
- **Hover:** the tick grows to 8 px.
- **Current page:** the item is Lime Ink, and its tick is a 10 px lit line.
- **Group labels:** uppercase mono, Subtle.

### Breadcrumb / page title
- **Parent crumbs:** 0.75rem uppercase mono, Muted.
- **Current page:** the page title in display type.
- **Phones** (below 768 px): the parent crumbs are hidden so the page title never truncates.

### Error pages
Standalone 404 and 500 pages (`templates/_error.html`), with no database or context processors:
- display headline;
- a plain message;
- the lit line;
- the error code as mono metadata (below the message, not above the heading);
- one "Back to the admin" button.

### Login
Unfold's form beside an authored SVG panel (`core/static/core/login-panel.svg`): the source's khaki 64 px grid lit by the lit line. Decorative, with no text. "Return to site" is removed, because `/` only redirects back to the login.

## Motion

State only, 120–180 ms, ease `cubic-bezier(.25,.46,.45,.94)`:
- hover and colour shifts;
- the nav tick growing;
- button press;
- skip-link reveal.

There are no page-load entrances (Operate surface). `prefers-reduced-motion` reduces every transition to near zero.

## Do's and Don'ts

### Do:
- **Do** put every new primary action on Lime Signal with #0C0C0C text.
- **Do** use Geist Mono for labels, statuses and numbers, and tabular figures in tables.
- **Do** keep status colours to red, amber, green and blue, one meaning each.
- **Do** run `impeccable detect` on changed pages. The glow is pre-approved only in `theme.css` and `templates/_error.html` (`.impeccable/config.json`).

### Don't:
- **Don't** add a second accent hue, gradient text, glass or drop shadows.
- **Don't** set labels, buttons or data in the display face.
- **Don't** put a kicker or eyebrow above a heading.
- **Don't** nest edged containers.
- **Don't** add page-load animation.
- **Don't** turn on `COMMAND.search_models`. It lists `str(obj)` for every model and would bypass per-role field hiding.

## Verification (2026-10-15)

- **impeccable detect:**
  - The login page is clean.
  - Signed-in pages show only Unfold-internal findings (filter-sheet nesting, `h1` → `h3` in the filter panel, hidden command-palette `kbd`s) and the sanctioned glow.
  - The contrast and hierarchy findings it raised were fixed.
- **Computed-style probe:**
  - the run button: lime on near-black;
  - checkboxes and switches: lime with a dark tick or thumb;
  - the add button: dark on lime.
- **taste-skill inspector (login):** its remaining flags are landing-page criteria (no photos, no motion) or the deliberate mono labels.
- **dembrandt `--compare` (users list vs benrey.io homepage):**
  - drift 84, expected, from product density (14–16 px UI vs 20–64 px marketing);
  - the same font families;
  - the palette matches apart from the intended hairline and subtle-grey shifts.
