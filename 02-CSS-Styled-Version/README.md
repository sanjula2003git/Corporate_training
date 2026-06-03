# Phase 2 — HTML + CSS Version

**ABC Learning Solutions — Training Management Portal**

> Goal: take the exact same app from Phase 1 and give it a **professional,
> responsive enterprise UI** using a **single shared stylesheet** — no
> Bootstrap, only Flexbox, CSS Grid, and Media Queries.

---

## File Structure

```
phase2-html-css/
├── index.html          # Login (gradient card, centered with Flexbox)
├── dashboard.html      # Cards (Grid) + activity panel + CSS bar chart
├── students.html       # Toolbar + styled table + add form
├── trainers.html       # Styled table + add form
├── courses.html        # Styled table + add form
├── attendance.html     # Course/date + checkbox table
├── certificates.html   # Status table with badges
├── reports.html        # Metric cards + completion table
└── styles.css          # ⭐ ONE stylesheet that styles ALL pages
```

## How to run

Double-click `index.html`. Log in (any text) → lands on the dashboard. No
build step or server required.

## Architecture

- Still **multi-page**, but every page now `<link>`s the **same `styles.css`**.
- **App shell** = Flexbox: `.sidebar` (fixed width) + `.main` (flexible).
- **Dashboard cards & forms** = CSS Grid with `auto-fit` / `minmax()` so they
  reflow automatically.
- **Design tokens** via CSS custom properties (`:root { --color-primary }`) —
  change a brand colour in one place, the whole app updates.

## Layout techniques used (no framework)

| Technique     | Where it's used                                  |
|---------------|--------------------------------------------------|
| Flexbox       | App shell, navbar, toolbar, login centering      |
| CSS Grid      | Dashboard cards, form fields, panel columns      |
| Media Queries | Sidebar collapses to a top bar under 720px       |
| Custom props  | Colours, spacing, radius, shadow (theming)       |

## Advantages of CSS

1. **Separation of concerns** — HTML = structure, CSS = presentation.
2. **Consistency** — one stylesheet guarantees every page looks identical.
3. **Maintainability** — restyle the whole app by editing one file.
4. **Responsiveness** — media queries adapt the layout to any screen.
5. **Reusability** — utility classes (`.btn`, `.card`, `.badge`) are reused
   everywhere instead of repeating inline styling.

## Separation of concerns — the key lesson

In Phase 1 the only way to change appearance was to edit markup on every page.
Here, the markup describes *what* each element is (`class="card"`) and the
stylesheet decides *how* it looks. Designers and developers can now work in
parallel on different files.

## Maintainability improvements vs Phase 1

- Brand colour change: **1 edit** (a CSS variable) vs editing every file.
- Consistent tables/buttons via shared classes instead of copy-paste.
- Responsive behaviour added with **zero** markup changes.

## Remaining limitation (the bridge to Phase 3)

The **sidebar and navbar are still copy-pasted into all 8 HTML pages.** CSS
solved *presentation* duplication but not *structural / markup* duplication,
and there is still **no real interactivity** (search, add, delete don't change
data). Solving those requires components and state → **React (Phase 3)**.
