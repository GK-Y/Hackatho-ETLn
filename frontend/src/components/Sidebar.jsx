// src/components/Sidebar.jsx
import React from "react";
import { NavLink } from "react-router-dom";
import * as Icons from "lucide-react"; // import the whole module

// Use icon names (strings) rather than direct component imports.
// This avoids ESM/CJS/export mismatches across library versions.
const items = [
  { to: "/dashboard", label: "Dashboard", iconName: "Home" },
  { to: "/sources", label: "Sources", iconName: "Archive" },
  { to: "/demo", label: "Demo Mode", iconName: "Zap" }, // use "Zap" if "Bolt" not available
];

// Helper to safely render an icon; fall back to a simple square if not found
function RenderIcon({ name, size = 18 }) {
  const Comp = Icons[name];
  if (typeof Comp === "function" || typeof Comp === "object") {
    // lucide-react exports components; render if present
    return <Comp size={size} />;
  }
  // fallback simple SVG
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      <rect width={size} height={size} rx="3" fill="#06b6d4" />
    </svg>
  );
}

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white h-screen border-r px-4 py-6">
      <div className="mb-8 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-white font-bold">ETL</div>
        <div>
          <div className="font-bold text-lg">Dynamic ETL</div>
          <div className="text-sm text-gray-500">Frontend Admin</div>
        </div>
      </div>

      <nav className="flex flex-col gap-1">
        {items.map((it) => (
          <NavLink
            key={it.to}
            to={it.to}
            className={({ isActive }) =>
              "flex items-center gap-3 px-3 py-2 rounded hover:bg-gray-50 " + (isActive ? "bg-gray-100 font-semibold" : "")
            }
          >
            <RenderIcon name={it.iconName} />
            <span>{it.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-8 text-sm text-gray-500">
        <div>Low-end optimized UI</div>
        <div className="mt-2">Lazy-load charts · Virtualized lists</div>
      </div>
    </aside>
  );
}
