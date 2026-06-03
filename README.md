# Training Management Portal — Frontend Evolution (SDLC Training)

**ABC Learning Solutions** runs corporate & student training programs and
currently manages Students, Trainers, Courses, Attendance, and Certificates
using spreadsheets and email. This project builds a centralized **Training
Management Portal** **three times** to teach how frontend development evolved:

```
TrainingManagementPortal/
├── phase1-plain-html/     # Plain HTML only (no CSS, no JS)
├── phase2-html-css/       # HTML + one shared CSS file (Flexbox/Grid/Media Queries)
└── phase3-react/          # React SPA (Router + components + hooks + mock data)
```

Each phase folder has its **own `README.md`** with full explanation, source,
and a comparison to the previous phase. Start there.

---

## The 8 modules (built in every phase)

1. Login · 2. Dashboard · 3. Student Management · 4. Trainer Management ·
5. Course Management · 6. Attendance Management · 7. Certificate Management ·
8. Reports Dashboard

## How to run each phase

| Phase | Command / action |
|-------|------------------|
| **1 — Plain HTML** | Double-click `phase1-plain-html/index.html` |
| **2 — HTML + CSS** | Double-click `phase2-html-css/index.html` |
| **3 — React** | `cd phase3-react` → `npm install` → `npm run dev` |

## Side-by-side comparison (the core teaching takeaway)

| Dimension          | Phase 1: Plain HTML        | Phase 2: HTML + CSS               | Phase 3: React SPA                         |
|--------------------|----------------------------|-----------------------------------|--------------------------------------------|
| **Concern split**  | structure only             | structure (HTML) + style (CSS)    | structure + style + behaviour (components) |
| **Styling**        | none (browser defaults)    | one shared stylesheet, themed     | shared CSS + component encapsulation       |
| **Layout**         | document flow              | Flexbox · Grid · Media Queries    | same CSS, applied via components           |
| **Navigation**     | full page reload per link  | full page reload per link         | instant client-side routing (SPA)          |
| **Duplication**    | nav repeated in 8 files    | **style** deduped; nav still in 8 | nav/UI written **once** as components       |
| **Interactivity**  | none                       | none (static)                     | live search, add, delete, save, feedback   |
| **Data**           | hard-coded markup          | hard-coded markup                 | JS state + mock service layer              |
| **Reusability**    | copy-paste                 | reusable CSS classes              | reusable components **+** classes          |
| **Maintainability**| edit every file            | edit one stylesheet               | edit one component / one data file         |
| **Scalability**    | painful, linear            | better for style, not structure   | add component + 1 route                     |
| **Performance**    | fastest to load, no UX     | fast, static                      | virtual DOM, code-split, no reloads        |

## The evolution narrative

1. **Plain HTML** structures content but mixes nothing else — and duplicates
   everything. → *CSS needed to separate presentation.*
2. **HTML + CSS** separates look from structure (one stylesheet restyles the
   whole app) but still duplicates markup and can't react to the user. →
   *Components + state needed.*
3. **React** introduces reusable components, a router, and state/hooks —
   solving structural duplication and enabling real interactivity, which is
   how modern enterprise frontends are built.

---
*Educational material for a Modern Application Development (SDLC) program.*
