// src/components/SmallStat.jsx
import React from "react";

export default function SmallStat({ title, value, hint }) {
  return (
    <div className="card flex flex-col">
      <div className="text-xs text-gray-500">{title}</div>
      <div className="text-2xl font-semibold">{value}</div>
      {hint && <div className="text-sm text-gray-400 mt-1">{hint}</div>}
    </div>
  );
}
