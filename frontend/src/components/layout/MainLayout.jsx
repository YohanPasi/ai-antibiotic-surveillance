import { Outlet } from "react-router-dom";
import { useState, useCallback } from "react";
import Header from "./Header";
import Sidebar from "./Sidebar";
import Footer from "./Footer";
import "./layout.css";

export default function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const toggleSidebar = useCallback(
    () => setSidebarOpen((prev) => !prev),
    []
  );

  return (
    <div className={`app-shell ${sidebarOpen ? "" : "sidebar-collapsed"}`}>
      <Header sidebarOpen={sidebarOpen} onToggleSidebar={toggleSidebar} />
      <div className="app-shell__main">
        <Sidebar isOpen={sidebarOpen} />
        <div className="app-shell__content">
          <Outlet />
        </div>
      </div>
      <Footer />
    </div>
  );
}

