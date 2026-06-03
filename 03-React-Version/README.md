# Phase 3 — React Version

**ABC Learning Solutions — Training Management Portal**

> Goal: rebuild the same app as a **component-based Single Page Application**
> with React Router, functional components, and hooks (`useState`,
> `useEffect`) — eliminating the duplication and lack of interactivity that
> remained after Phase 2.

---

## Folder Structure

```
phase3-react/
├── index.html              # single HTML host page
├── package.json
├── vite.config.js
└── src/
    ├── main.jsx            # entry — mounts <App/> inside <BrowserRouter>
    ├── App.jsx             # route table (React Router)
    ├── components/         # REUSABLE building blocks
    │   ├── Layout.jsx      # shared shell (Sidebar + Navbar + <Outlet/>)
    │   ├── Sidebar.jsx     # written ONCE, used on every page
    │   ├── Navbar.jsx
    │   ├── DashboardCard.jsx
    │   ├── StudentTable.jsx
    │   ├── TrainerTable.jsx
    │   ├── CourseTable.jsx
    │   ├── AttendanceForm.jsx
    │   ├── CertificateList.jsx
    │   └── ReportsPanel.jsx
    ├── pages/              # one component per route
    │   ├── Login.jsx
    │   ├── Dashboard.jsx
    │   ├── Students.jsx
    │   ├── Trainers.jsx
    │   ├── Courses.jsx
    │   ├── Attendance.jsx
    │   ├── Certificates.jsx
    │   └── Reports.jsx
    ├── services/
    │   └── mockData.js     # mock JSON + fake async fetch (no backend)
    └── styles/
        └── global.css
```

## How to run

```bash
cd phase3-react
npm install
npm run dev
```

Open the printed URL (e.g. http://localhost:5173). Log in → explore. Try:
- **Students:** type in the search box (live filtering), add a student, delete one.
- **Attendance:** toggle checkboxes, save → confirmation badge.
- **Certificates:** Generate is enabled only for *Completed* courses.

## React concepts demonstrated

| Concept                | Where                                                        |
|------------------------|-------------------------------------------------------------|
| **Functional components** | every `.jsx` file                                        |
| **React Router**       | `App.jsx` routes + `Sidebar` `NavLink` + `useNavigate`      |
| **Nested routes / layout** | `App.jsx` `<Route element={<Layout/>}>` + `<Outlet/>`  |
| **useState**           | forms, search query, attendance checkboxes, lists           |
| **useEffect**          | `Students/Trainers/Courses` load data on mount              |
| **Props**              | `DashboardCard`, all tables receive data + callbacks        |
| **Lifting state up**   | pages own data; tables raise `onDelete` / `onGenerate`      |
| **Controlled inputs**  | every input binds `value` + `onChange`                      |
| **Mock service layer** | `services/mockData.js` (`fetchData` returns a Promise)      |

## Architecture

- **Single Page Application:** one `index.html`; React swaps page content in
  place via the Router — no full page reloads, so navigation is instant.
- **Component tree:** `App → Layout → (Sidebar, Navbar, page)`. Each page
  composes small reusable components.
- **Unidirectional data flow:** state lives in the page; data flows *down* via
  props; events flow *up* via callbacks.

## Reusability

`DashboardCard` is rendered 8 times (Dashboard + Reports) from one definition.
`Sidebar`/`Navbar` exist once instead of being copy-pasted into 8 HTML files
(Phase 1 & 2). Tables are generic — give them `rows` and an `onDelete`.

## Maintainability

- Add a nav link? Edit the `links` array in **one** file (`Sidebar.jsx`).
- Change the card look? Edit `DashboardCard.jsx` once; all 8 update.
- Data source swap (mock → real API)? Change only `services/mockData.js`;
  components are untouched because they depend on the service, not the source.

## Scalability

- New screen = new page component + one `<Route>`. Linear, isolated growth.
- Clear separation: `pages/` (screens) · `components/` (UI) · `services/`
  (data) · `styles/` (CSS). Teams can work in parallel without collisions.

## Performance considerations

- **SPA navigation** avoids full-page reloads (only the changed component
  re-renders).
- React's **virtual DOM** updates only what actually changed (e.g. typing in
  search re-renders just the table rows).
- Production builds are **bundled, minified, and code-split** by Vite.
- Further gains available with `React.memo`, `useMemo`, lazy routes
  (`React.lazy`) as the app grows.

## Comparison with Phase 2

| Aspect            | Phase 2 (HTML+CSS)               | Phase 3 (React)                       |
|-------------------|----------------------------------|---------------------------------------|
| Nav/sidebar       | copy-pasted into 8 files         | **one** `Sidebar` component           |
| Interactivity     | none (static)                    | live search, add, delete, save        |
| Data              | hard-coded in markup             | JS state + mock service layer         |
| Navigation        | full page reloads                | instant SPA routing                   |
| Reuse             | CSS classes only                 | CSS **+ components**                   |
| Scaling a screen  | new full HTML file               | new component + one route line        |
