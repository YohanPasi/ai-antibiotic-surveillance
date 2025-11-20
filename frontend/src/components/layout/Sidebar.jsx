import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../auth/useAuth";

const ICONS = {
  grid: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1.5" y="1.5" width="5" height="5" rx="1" stroke="currentColor" />
      <rect x="9.5" y="1.5" width="5" height="5" rx="1" stroke="currentColor" />
      <rect x="1.5" y="9.5" width="5" height="5" rx="1" stroke="currentColor" />
      <rect x="9.5" y="9.5" width="5" height="5" rx="1" stroke="currentColor" />
    </svg>
  ),
  shield: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path
        d="M8 1.5l5 2v4.4c0 3.1-2.16 5.62-5 6.6-2.84-.98-5-3.5-5-6.6V3.5l5-2z"
        stroke="currentColor"
        strokeLinejoin="round"
      />
    </svg>
  ),
  lab: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path
        d="M5 1.5h6M7 1.5v5.2L3.5 13c-.4.7.1 1.5.9 1.5h7.2c.8 0 1.3-.8.9-1.5L9 6.7V1.5"
        stroke="currentColor"
        strokeLinejoin="round"
      />
    </svg>
  ),
  layers: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path
        d="M2 6.5l6-3 6 3-6 3-6-3zM2 10l6 3 6-3"
        stroke="currentColor"
        strokeLinejoin="round"
      />
    </svg>
  ),
  flask: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path
        d="M5.5 2h5M6 2v4.5L3 12.5c-.5.8.2 1.5 1 1.5h8c.8 0 1.5-.7 1-1.5L10 6.5V2"
        stroke="currentColor"
        strokeLinejoin="round"
      />
      <circle cx="8" cy="13" r="1" fill="currentColor" />
    </svg>
  ),
};

const sections = [
  {
    title: "Dashboards",
    icon: "layers",
    items: [
      { label: "Command", short: "CC", path: "/modules", icon: "grid" },
      { label: "MRSA", short: "MR", path: "/mrsa", icon: "shield" },
      { label: "ESBL", short: "ES", path: "/esbl", icon: "lab" },
      { label: "Non-Fermenter", short: "NF", path: "/nonfermenter", icon: "flask" },
    ],
  },
];

export default function Sidebar({ isOpen }) {
  const { user } = useAuth();
  const [expandedSections, setExpandedSections] = useState(() =>
    sections.reduce((acc, section) => {
      acc[section.title] = false;
      return acc;
    }, {})
  );

  function toggleSection(title) {
    setExpandedSections((prev) => ({
      ...prev,
      [title]: !prev[title],
    }));
  }

  return (
    <aside className={`sidebar ${isOpen ? "open" : "collapsed"}`}>
      {sections.map((section) => (
        <div
          className={`sidebar__section ${
            expandedSections[section.title] ? "sidebar__section--open" : ""
          }`}
          key={section.title}
        >
          <button
            type="button"
            className="sidebar__section-toggle"
            aria-expanded={expandedSections[section.title]}
            onClick={() => toggleSection(section.title)}
          >
            <span className="sidebar__section-icon" aria-hidden="true">
              {ICONS[section.icon]}
            </span>
            <span className="sidebar__title">{section.title}</span>
            <span
              className={`sidebar__section-indicator ${
                expandedSections[section.title] ? "is-open" : ""
              }`}
              aria-hidden="true"
            />
          </button>
          <div
            className={`sidebar__section-content ${
              expandedSections[section.title] ? "is-open" : ""
            }`}
          >
            <nav className="sidebar__links">
              {section.items.map((item) => {
                const disabled = !user;
                return (
                  <NavLink
                    key={item.label}
                    to={item.path}
                    aria-label={item.label}
                    data-short={item.short}
                    className={({ isActive }) =>
                      [
                        "sidebar__link",
                        isActive ? "sidebar__link--active" : "",
                        disabled ? "sidebar__link--disabled" : "",
                      ]
                        .filter(Boolean)
                        .join(" ")
                    }
                    aria-disabled={disabled}
                    onClick={(e) => {
                      if (disabled) e.preventDefault();
                    }}
                  >
                    <span className="sidebar__icon" aria-hidden="true">
                      {ICONS[item.icon]}
                    </span>
                    <span className="sidebar__link-label">{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>
        </div>
      ))}

      {!user && (
        <div className="sidebar__hint">
          Sign in to access clinical analytics.
        </div>
      )}
    </aside>
  );
}
