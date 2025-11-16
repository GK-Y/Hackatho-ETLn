// src/pages/DemoMode.jsx
import React, { useState } from "react";
import JsonViewer from "../components/JsonViewer";
import SmallStat from "../components/SmallStat";
import { Link } from "react-router-dom";

/**
 * Lightweight client-side demo mode:
 * Single demo source with small mock data to exercise UI without backend.
 */

const DEMO_SOURCE = {
  source_id: "demo_local",
  last_ingest: new Date().toISOString(),
  record_count: 12,
  schema_version: 1,
  chunks: 6
};

const DEMO_RECORDS = Array.from({ length: 12 }).map((_, i) => ({
  id: `demo_${i}`,
  name: ["Alice", "Bob", "Carol", "Dave"][i % 4],
  amount: Math.round(Math.random() * 1000),
  category: ["sales", "support", "engineering"][i % 3],
  ts: new Date(Date.now() - i * 1000 * 60 * 60).toISOString()
}));

const DEMO_SUMMARY = {
  chunk_types: [{ type: "csv", count: 4 }, { type: "text", count: 2 }],
  top_fields: [{ field: "id", count: 12 }, { field: "name", count: 12 }, { field: "amount", count: 12 }],
  schema_history: [{ field_count: 4 }],
  top_tokens: [{ token: "demo", count: 12 }, { token: "alice", count: 3 }]
};

export default function DemoMode() {
  const [mode] = useState("demo");

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl">Demo Mode</h2>
          <div className="text-sm text-gray-500">Use this offline demo to show judges features without running backend.</div>
        </div>
        <div>
          <Link to={`/records/${DEMO_SOURCE.source_id}`} className="px-3 py-1 bg-primary text-white rounded mr-2">Open Demo Records</Link>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <SmallStat title="Demo Source" value={DEMO_SOURCE.source_id} />
        <SmallStat title="Records" value={DEMO_SOURCE.record_count} />
        <SmallStat title="Chunks" value={DEMO_SOURCE.chunks} />
      </div>

      <div className="card">
        <h4 className="font-semibold">Sample records</h4>
        <div className="mt-3 grid grid-cols-3 gap-3">
          {DEMO_RECORDS.map(r => (
            <div className="p-3 border rounded" key={r.id}>
              <div className="font-mono text-sm">{r.id}</div>
              <div className="text-sm">{r.name}</div>
              <div className="text-sm text-gray-500">Amt: {r.amount}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 card">
        <h4 className="font-semibold">Demo Visual Summary</h4>
        <div className="mt-3">
          <JsonViewer data={DEMO_SUMMARY} />
        </div>
      </div>
    </div>
  );
}
