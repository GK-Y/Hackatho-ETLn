// src/pages/Schema.jsx
import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getSchema, getSchemaHistory } from "../api/client";
import JsonViewer from "../components/JsonViewer";

const DEMO_SCHEMA = {
  source_id: "demo_local",
  version: 1,
  fields: {
    id: { type: "string", presence: 24 },
    name: { type: "string", presence: 24 },
    amount: { type: "number", presence: 24 },
    category: { type: "string", presence: 24 }
  },
  created_at: new Date().toISOString()
};

function diffSchemas(a, b) {
  const af = a?.fields ? Object.keys(a.fields) : [];
  const bf = b?.fields ? Object.keys(b.fields) : [];
  const added = bf.filter((x) => !af.includes(x));
  const removed = af.filter((x) => !bf.includes(x));
  return { added, removed };
}

export default function Schema() {
  const { sourceId } = useParams();
  const isDemo = sourceId && String(sourceId).toLowerCase().startsWith("demo");

  const [schema, setSchema] = useState(null);
  const [history, setHistory] = useState([]);
  const [diff, setDiff] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setError(null);
      if (isDemo) {
        if (mounted) {
          setSchema(DEMO_SCHEMA);
          setHistory([DEMO_SCHEMA]);
          setDiff({ added: [], removed: [] });
        }
        return;
      }
      try {
        const s = await getSchema(sourceId);
        if (!s.error) setSchema(s.data);
        const h = await getSchemaHistory(sourceId);
        if (!h.error) {
          setHistory(h.data || []);
          if ((h.data || []).length >= 2) {
            setDiff(diffSchemas(h.data[h.data.length - 2], h.data[h.data.length - 1]));
          } else {
            setDiff({ added: [], removed: [] });
          }
        }
      } catch (e) {
        setError(String(e));
      }
    }
    load();
    return () => (mounted = false);
  }, [sourceId, isDemo]);

  return (
    <div>
      <h2 className="text-2xl mb-4">Schema — {sourceId}</h2>
      {error && <div className="text-red-600 mb-2">Error: {String(error)}</div>}
      <div className="grid grid-cols-2 gap-4">
        <div className="card">
          <h4 className="font-semibold">Latest Schema</h4>
          <div className="mt-3">
            <JsonViewer data={schema} />
          </div>
        </div>
        <div className="card">
          <h4 className="font-semibold">Schema History</h4>
          <div className="mt-3">
            {history.length === 0 && <div className="text-sm text-gray-500">No history</div>}
            {history.map((h, i) => (
              <div key={i} className="mb-2 p-2 border rounded text-xs">
                <div className="font-mono text-sm">version {i + 1} — {h.created_at || "unknown"}</div>
                <div className="text-xs text-gray-600">fields: {h.fields ? Object.keys(h.fields).length : (h.field_count || "?")}</div>
              </div>
            ))}
          </div>
          {diff && (
            <div className="mt-4">
              <h5 className="font-semibold">Diff (last two)</h5>
              <div className="text-sm">
                <div className="text-green-700">Added: {diff.added.join(", ") || "None"}</div>
                <div className="text-red-600">Removed: {diff.removed.join(", ") || "None"}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
