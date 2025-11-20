import { useAuth } from "../../auth/useAuth";

export default function Header({ sidebarOpen, onToggleSidebar }) {
  const { user, logout } = useAuth();
  const displayName =
    user?.full_name || user?.username || user?.email || "Guest user";

  return (
    <header className="header">
      <button
        type="button"
        className="header__toggle"
        aria-label={sidebarOpen ? "Collapse navigation" : "Expand navigation"}
        onClick={onToggleSidebar}
      >
        <span />
        <span />
        <span />
      </button>

      <div className="header__brand">
        <div className="header__logo">🧬</div>
        <div className="header__meta">
          <p className="header__title">AI-Driven Resistance Command Center</p>
          <p className="header__subtitle">Teaching Hospital Peradeniya · SLIIT</p>
          <span className="header__badge">
            <span aria-hidden="true">●</span> Live surveillance
          </span>
        </div>
      </div>

      <div className="header__actions">
        <div className="header__user">
          <span>{displayName}</span>
          <small>{user ? "Secure clinician session" : "Limited preview"}</small>
        </div>
        {user && (
          <button type="button" className="header__button" onClick={logout}>
            Logout
          </button>
        )}
      </div>
    </header>
  );
}
