// src/components/Topbar.jsx
import React from "react";
import { Link } from "react-router-dom";

export default function Topbar() {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b bg-white">
      <div className="flex items-center gap-4">
        <a className="sr-only" href="#content">Skip to content</a>
        <div className="text-xl font-bold">Dynamic ETL — Frontend</div>
        <div className="text-sm text-gray-500">Fast judge demo · optimized for Pentium Gold</div>
      </div>
      <div className="flex items-center gap-3">
        <Link to="/visualize/test_source" className="text-sm px-3 py-1 rounded bg-primary text-white">Quick Visualize</Link>
        <button className="text-sm px-3 py-1 rounded border">Settings</button>
      </div>
    </header>
  );
}
