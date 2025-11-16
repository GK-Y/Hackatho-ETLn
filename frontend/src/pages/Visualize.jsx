// src/pages/Visualize.jsx
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getVisualizeSummary, getRecords } from "../api/client";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  LineChart,
  Line
} from "recharts";

const COLORS = ["#06b6d4", "#60a5fa", "#34d399", "#f97316", "#f43f5e", "#a78bfa"];

// Lightweight demo summary used when sourceId is demo_local or when backend has no data
const DEMO_SUMMARY = {
  chunk_types: [
    { type: "csv", count: 4 },
    { type: "text", count: 2 }
  ],
  top_fields: [
    { field: "id", count: 12 },
    { field: "name", count: 11 },
    { field: "amount", count: 9 },
    { field: "category", count: 7 }
  ],
  schema_history: [
    { version_label: "v1", field_count: 4, created_at: new Date().toISOString() }
  ],
  top_tokens: [
    { token: "demo", count: 12 },
    { token: "alice", count: 3 },
    { token: "bob", count: 2 }
  ]
};

function TokenCloud({ tokens }) {
  if (!tokens || tokens.length === 0) return <div className="text-sm text-gray-500">No tokens available</div>;
  const max = Math.max(...tokens.map((t) => t.count));
  return (
    <div className="flex flex-wrap gap-2">
      {tokens.slice(0, 60).map((t, i) => {
        const size = 12 + Math.round((t.count / max) * 18);
        return (
          <span key={t.token + i} style={{ fontSize: size }} className="inline-block p-1">
            {t.token}
          </span>
        );
      })}
    </div>
  );
}

export default function Visualize() {
  const { sourceId } = useParams();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setErrorMsg(null);
      setSummary(null);

      // If this looks like demo source, use local demo summary
      if (sourceId && String(sourceId).toLowerCase().startsWith("demo")) {
        if (mounted) {
          setSummary(DEMO_SUMMARY);
          setLoading(false);
        }
        return;
      }

      // Normal path: call backend summary endpoint
      try {
        const res = await getVisualizeSummary(sourceId);
        if (res.error) {
          // backend may return 404 if source not found
          setErrorMsg(res.error && res.error.detail ? res.error.detail : String(res.error));
          // Try fallback: fetch some records (conservative) and compute light summary
          try {
            const rec = await getRecords(sourceId, 200, 0);
            if (!rec.error && rec.data && rec.data.length > 0) {
              // compute top fields from sample
              const counts = {};
              rec.data.forEach((d) => {
                Object.keys(d || {}).forEach((k) => {
                  counts[k] = (counts[k] || 0) + 1;
                });
              });
              const fallback = {
                chunk_types: [],
                top_fields: Object.keys(counts).map((k) => ({ field: k, count: counts[k] })).sort((a, b) => b.count - a.count).slice(0, 30),
                schema_history: [],
                top_tokens: []
              };
              setSummary(fallback);
              setLoading(false);
              return;
            }
          } catch (e) {
            // ignore fallback errors
          }
          // Nothing found
          setSummary(null);
          setLoading(false);
          return;
        }
        // success
        setSummary(res.data || null);
      } catch (e) {
        setErrorMsg(String(e));
        setSummary(null);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => (mounted = false);
  }, [sourceId]);

  if (loading) {
    return (
      <div className="card">
        <div className="skeleton h-40" />
      </div>
    );
  }

  if (!summary) {
    return (
      <div>
        <h2 className="text-2xl mb-4">Visualize — {sourceId}</h2>
        <div className="card">
          <div className="text-sm text-gray-600">
            No visualization summary available for <span className="font-mono">{sourceId}</span>.
            {errorMsg && <div className="text-red-600 mt-2">Error: {String(errorMsg)}</div>}
            <div className="mt-2">
              Possible reasons: the dataset doesn't exist in the backend or the backend returned 404.
            </div>
            <div className="mt-3 text-sm">
              Try uploading a file for this source or open <a href="/demo" className="text-primary">Demo Mode</a>.
            </div>
          </div>
        </div>
      </div>
    );
  }

  const chunkTypes = summary.chunk_types || [];
  const topFields = summary.top_fields || [];
  const schemaHistory = summary.schema_history || [];

  return (
    <div>
      <h2 className="text-2xl mb-4">Visualize — {sourceId}</h2>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="card col-span-1">
          <h4 className="font-semibold text-sm">Chunk Types</h4>
          <div style={{ height: 200 }} className="mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={chunkTypes} dataKey="count" nameKey="type" outerRadius={70} label>
                  {chunkTypes.map((entry, idx) => (
                    <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card col-span-1">
          <h4 className="font-semibold text-sm">Top Fields</h4>
          <div style={{ height: 200 }} className="mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topFields}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="field" />
                <YAxis />
                <Bar dataKey="count">
                  {topFields.map((f, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card col-span-1">
          <h4 className="font-semibold text-sm">Schema Evolution</h4>
          <div style={{ height: 200 }} className="mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={(schemaHistory || []).map((s, i) => ({
                  version: i + 1,
                  fields: s.field_count || 0
                }))}
              >
                <XAxis dataKey="version" />
                <YAxis />
                <Line type="monotone" dataKey="fields" stroke="#06b6d4" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="card">
        <h4 className="font-semibold">Token Cloud</h4>
        <div className="mt-3">
          <TokenCloud tokens={summary.top_tokens || []} />
        </div>
      </div>
    </div>
  );
}
