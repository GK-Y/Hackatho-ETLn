// src/components/JsonViewer.jsx
import React from "react";

function pretty(obj) {
  try {
    return JSON.stringify(obj, null, 2);
  } catch (e) {
    return String(obj);
  }
}

export default function JsonViewer({ data, compact = false }) {
  if (!data) return <pre className="p-2 text-sm text-gray-500">No data</pre>;
  return (
    <pre className="max-h-[60vh] overflow-auto bg-gray-50 p-3 rounded text-sm">
      <code>{compact ? JSON.stringify(data) : pretty(data)}</code>
    </pre>
  );
}
