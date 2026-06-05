// Entry point — mounts the React app into #root and wraps it in the Router.
import React from "react";
import ReactDOM from "react-dom/client";
// HashRouter is used (instead of BrowserRouter) so the app works correctly
// when hosted as static files on GitHub Pages — no server-side routing needed.
import { HashRouter } from "react-router-dom";
import App from "./App.jsx";
import "./styles/global.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </React.StrictMode>
);
