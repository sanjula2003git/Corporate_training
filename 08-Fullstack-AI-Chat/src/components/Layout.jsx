// Layout.jsx — the shared app shell. Sidebar + Navbar are rendered once here;
// <Outlet/> is where the active page is injected by React Router.
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar.jsx";
import Navbar from "./Navbar.jsx";
import ChatWidget from "./ChatWidget.jsx";

export default function Layout() {
  return (
    <div className="app">
      <Sidebar />
      <div className="main">
        <Navbar />
        <div className="content">
          <Outlet />
        </div>
      </div>
      {/* Floating support chat — shows only for students & trainers */}
      <ChatWidget />
    </div>
  );
}
