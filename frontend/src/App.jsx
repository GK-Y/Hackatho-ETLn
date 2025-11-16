// src/App.jsx
import React, { Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Sources from "./pages/Sources";
import Records from "./pages/Records";
import Visualize from "./pages/Visualize";
import Schema from "./pages/Schema";
import DemoMode from "./pages/DemoMode";

export default function App() {
  return (
    <Layout>
      <Suspense fallback={<div className="p-6">Loading...</div>}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/sources" element={<Sources />} />
          <Route path="/records/:sourceId" element={<Records />} />
          <Route path="/visualize/:sourceId" element={<Visualize />} />
          <Route path="/schema/:sourceId" element={<Schema />} />
          <Route path="/demo" element={<DemoMode />} />
        </Routes>
      </Suspense>
    </Layout>
  );
}
