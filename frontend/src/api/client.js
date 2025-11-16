// src/api/client.js
const BASE = "http://127.0.0.1:8000";

async function safeFetch(url, opts = {}) {
  try {
    const res = await fetch(url, {
      headers: { "Accept": "application/json" },
      ...opts
    });
    const text = await res.text();
    // try parse json
    try {
      const json = text ? JSON.parse(text) : null;
      if (!res.ok) return { error: json || text || res.statusText, status: res.status };
      return { data: json, status: res.status };
    } catch (e) {
      // non-json response
      if (!res.ok) return { error: text || res.statusText, status: res.status };
      return { data: text, status: res.status };
    }
  } catch (err) {
    return { error: err.message || "Network error" };
  }
}

export async function getSources() {
  return safeFetch(`${BASE}/sources`);
}

export async function getVisualizeSummary(sourceId) {
  return safeFetch(`${BASE}/visualize/summary?source_id=${encodeURIComponent(sourceId)}`);
}

export async function getSchema(sourceId) {
  return safeFetch(`${BASE}/schema?source_id=${encodeURIComponent(sourceId)}`);
}

export async function getSchemaHistory(sourceId) {
  return safeFetch(`${BASE}/schema/history?source_id=${encodeURIComponent(sourceId)}`);
}

export async function getRecords(sourceId, limit = 100, page = 0) {
  const url = `${BASE}/records?source_id=${encodeURIComponent(sourceId)}&limit=${limit}&page=${page}`;
  return safeFetch(url);
}

export async function postBackup(sourceId) {
  return safeFetch(`${BASE}/backup?source_id=${encodeURIComponent(sourceId)}`, { method: "POST" });
}

export async function deleteDataset(sourceId, confirm = 1) {
  return safeFetch(`${BASE}/dataset?source_id=${encodeURIComponent(sourceId)}&confirm=${confirm}`, { method: "DELETE" });
}

export async function getTestFiles() {
  return safeFetch(`${BASE}/test-files`);
}

export async function postProcessFile(filename) {
  // filename must be just the basename
  return safeFetch(`${BASE}/process-file?filename=${encodeURIComponent(filename)}`, { method: "POST" });
}

// client upload helper (upload local file to backend /upload)
export async function uploadLocalFile(file, sourceId) {
  try {
    const fd = new FormData();
    fd.append("file", file, file.name);
    fd.append("source_id", sourceId || file.name.split(".")[0]);
    const res = await fetch(`${BASE}/upload`, { method: "POST", body: fd });
    const text = await res.text();
    try {
      const json = text ? JSON.parse(text) : null;
      if (!res.ok) return { error: json || text, status: res.status };
      return { data: json, status: res.status };
    } catch (e) {
      if (!res.ok) return { error: text || res.statusText, status: res.status };
      return { data: text, status: res.status };
    }
  } catch (err) {
    return { error: err.message || "Network error" };
  }
}

