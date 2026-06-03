# Phase 1 — Plain HTML Version

**ABC Learning Solutions — Training Management Portal**

> Goal: show students how web applications were *traditionally* structured —
> before CSS and JavaScript — using **only semantic HTML**.

---

## File Structure

```
phase1-plain-html/
├── index.html          # Landing / navigation hub
├── login.html          # Login form
├── dashboard.html      # Summary cards + recent activity + chart placeholder
├── students.html       # Student table + add/search forms
├── trainers.html       # Trainer table + add form
├── courses.html        # Course table + add form
├── attendance.html     # Course dropdown, date, present checkboxes
├── certificates.html   # Certificate status table
└── reports.html        # Metric cards + completion table
```

Each page is **fully independent**. There is no shared layout — every page
repeats its own `<header>` and `<nav>`. This is the defining characteristic
(and the core weakness) of the plain-HTML era.

## How to run

Just **double-click any `.html` file** — it opens in the browser. No build
step, no server, no dependencies.

## Architecture

- **Multi-page, server-navigation model.** Every link is a full page load.
- **Semantic tags** carry all the meaning: `<header>`, `<nav>`, `<main>`,
  `<section>`, `<article>`, `<table>`, `<form>`, `<fieldset>`, `<footer>`.
- **No state.** Forms `POST`/`GET` to a page; in a real app a *server* would
  process them. Here they just navigate.

## Advantages

1. **Zero dependencies** — works in any browser, forever.
2. **Extremely fast to load** — no CSS/JS parsing.
3. **Accessible by default** — semantic HTML is readable by screen readers.
4. **Easy to learn** — the document *is* the content.
5. **SEO-friendly** — search engines read pure markup easily.

## Limitations

1. **No visual design** — everything is browser-default black-on-white.
2. **Massive duplication** — the nav bar is copy-pasted into 8 files. Change
   one link → edit 8 files.
3. **No interactivity** — no live search, no instant validation, no charts.
4. **No responsiveness** — layout cannot adapt to screen size.
5. **Poor maintainability** — the app grows linearly in pain as pages multiply.

## Why CSS became necessary

HTML answers *“what is this content?”* but not *“how should it look?”*. As
business apps needed branding, layout, spacing, and responsive behaviour,
mixing presentation into markup (`<font>`, `<table>` layouts, `bgcolor`)
became unmaintainable. **CSS** was introduced to *separate presentation from
structure* — letting one stylesheet restyle every page at once.

➡️ Continue to **Phase 2 (HTML + CSS)** to see the same app gain a
professional, responsive UI from a single shared stylesheet.
