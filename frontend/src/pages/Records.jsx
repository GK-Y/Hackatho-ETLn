// src/pages/Records.jsx
import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { getRecords, getSchema } from "../api/client";
import { FixedSizeList as List } from "react-window";
import JsonViewer from "../components/JsonViewer";

/**
 * Demo records used when sourceId looks like a demo (e.g., demo_local)
 * Keeps demo lightweight and offline so judges can interact without backend.
 */
const DEMO_RECORDS = Array.from({ length: 24 }).map((_, i) => ({
  _id: `demo_${i}`,
  id: `demo_${i}`,
  name: ["Alice", "Bob", "Carol", "Dave"][i % 4],
  amount: Math.round(Math.random() * 1000),
  category: ["sales", "support", "engineering"][i % 3],
  ts: new Date(Date.now() - i * 1000 * 60 * 60).toISOString()
}));

export default function Records() {
  const { sourceId } = useParams();
  const isDemo = sourceId && String(sourceId).toLowerCase().startsWith("demo");

  const [loading, setLoading] = useState(true);
  const [records, setRecords] = useState([]);
  const [page, setPage] = useState(0);
  const [limit] = useState(100);
  const [selected, setSelected] = useState(null);
  const [schema, setSchema] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      setSelected(null);
      setSchema(null);
      if (isDemo) {
        if (mounted) {
          setRecords(DEMO_RECORDS);
          setSchema({ demo: true, fields: Object.keys(DEMO_RECORDS[0] || {}) });
          setLoading(false);
        }
        return;
      }
      try {
        const s = await getSchema(sourceId);
        if (!s.error) setSchema(s.data);
        const r = await getRecords(sourceId, limit, page);
        if (!r.error) setRecords(r.data || []);
        else {
          setError(r.error);
          setRecords([]);
        }
      } catch (e) {
        setError(String(e));
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => (mounted = false);
  }, [sourceId, page, limit, isDemo]);

  const columns = useMemo(() => {
    if (!schema) return ["_raw"];
    if (schema?.fields && Array.isArray(schema.fields)) return schema.fields.map((f) => (typeof f === "string" ? f : f.name));
    if (schema?.fields && typeof schema.fields === "object") return Object.keys(schema.fields);
    return ["_raw"];
  }, [schema]);

  function Row({ index, style }) {
    const item = records[index];
    if (!item) return <div style={style} className="p-2">—</div>;
    return (
      <div style={style} className="flex items-center border-b p-2">
        <div className="w-64 font-mono text-sm">{item.id || item._id || `#${index}`}</div>
        <div className="flex-1 text-sm text-gray-700 truncate">{JSON.stringify(item).slice(0, 120)}</div>
        <div className="ml-2 flex gap-2">
          <button className="px-2 py-1 text-sm border rounded" onClick={() => setSelected(item)}>Inspect</button>
          <button className="px-2 py-1 text-sm border rounded" onClick={() => {
            const blob = new Blob([JSON.stringify(item, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${sourceId}_record_${index}.json`;
            a.click();
            URL.revokeObjectURL(url);
          }}>Download</button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl mb-4">Records — {sourceId}</h2>

      <div className="card">
        {loading ? (
          <div className="skeleton h-40" />
        ) : (
          <>
            {error && <div className="text-red-600 mb-2 text-sm">Error: {String(error)}</div>}
            <div className="mb-2 text-sm text-gray-500">Showing up to {limit} records (page {page + 1}). Virtualized list keeps UI fast.</div>
            <div style={{ height: 400 }}>
              <List height={400} itemCount={records.length} itemSize={64} width={"100%"}>
                {Row}
              </List>
            </div>

            <div className="flex items-center justify-between mt-3">
              <div>
                <button className="px-3 py-1 mr-2 border rounded" onClick={() => setPage((p) => Math.max(0, p - 1))}>Prev</button>
                <button className="px-3 py-1 border rounded" onClick={() => setPage((p) => p + 1)}>Next</button>
              </div>
              <div className="text-sm text-gray-500">Records: {records.length}</div>
            </div>
          </>
        )}
      </div>

      {selected && (
        <div className="card mt-4">
          <div className="flex justify-between items-start">
            <h3 className="font-semibold">Record Inspect</h3>
            <button onClick={() => setSelected(null)} className="px-2 py-1 border rounded">Close</button>
          </div>
          <JsonViewer data={selected} />
        </div>
      )}
    </div>
  );
}
