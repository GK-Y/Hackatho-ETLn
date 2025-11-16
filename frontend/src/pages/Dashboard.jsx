// src/pages/Dashboard.jsx
import React, { useEffect, useState } from "react";
import { getSources, getTestFiles, postProcessFile, uploadLocalFile } from "../api/client";
import SmallStat from "../components/SmallStat";
import { LineChart, Line, ResponsiveContainer } from "recharts";

export default function Dashboard() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);

  // test files UI state
  const [testFiles, setTestFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState("");
  const [processingStatus, setProcessingStatus] = useState(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      const s = await getSources();
      if (mounted) {
        if (!s.error) setSources(s.data || []);
        else setSources([]);
        setLoading(false);
      }
    }
    load();
    return () => (mounted = false);
  }, []);

  useEffect(() => {
    // load test files list (lightweight)
    let mounted = true;
    getTestFiles().then((res) => {
      if (!mounted) return;
      if (!res.error && Array.isArray(res.data)) {
        setTestFiles(res.data);
        if (res.data.length > 0) setSelectedFile(res.data[0].name);
      } else {
        setTestFiles([]);
      }
    });
    return () => (mounted = false);
  }, []);

  async function handleProcessFile() {
    if (!selectedFile) return alert("Select a test file first");
    setProcessingStatus({ status: "starting", msg: `Starting processing ${selectedFile}...` });
    const res = await postProcessFile(selectedFile);
    if (res.error) {
      setProcessingStatus({ status: "error", msg: String(res.error) });
    } else {
      setProcessingStatus({ status: "started", msg: `Processing started for source_id=${res.data?.source_id || res.data?.source}` });
      // Optionally poll sources after a short delay to refresh stats
      setTimeout(() => {
        getSources().then((s) => { if (!s.error) setSources(s.data || []); });
      }, 3000);
    }
  }

  async function handleUploadLocal(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    setUploading(true);
    setProcessingStatus({ status: "uploading", msg: `Uploading ${file.name}...` });
    const res = await uploadLocalFile(file);
    if (res.error) {
      setProcessingStatus({ status: "error", msg: String(res.error) });
    } else {
      setProcessingStatus({ status: "uploaded", msg: `Uploaded as source_id=${res.data?.source_id || file.name.split(".")[0]}` });
      // refresh sources after a delay
      setTimeout(() => { getSources().then((s) => { if (!s.error) setSources(s.data || []); }); }, 2000);
    }
    setUploading(false);
    // reset input
    e.target.value = "";
  }

  const totalSources = sources.length;
  const totalRecords = sources.reduce((s, a) => s + (a.record_count || 0), 0);
  const totalChunks = sources.reduce((s, a) => s + (a.chunks || 0), 0);
  const lastIngest = sources.reduce((latest, s) => {
    if (!s.last_ingest) return latest;
    const t = new Date(s.last_ingest).getTime();
    return t > latest ? t : latest;
  }, 0);

  const sparkData = (sources || []).slice(-10).map((s, i) => ({ i, c: s.record_count || 0 }));

  return (
    <div id="content">
      <div className="grid grid-cols-4 gap-4 mb-6">
        <SmallStat title="Sources" value={loading ? "—" : totalSources} />
        <SmallStat title="Total Records" value={loading ? "—" : totalRecords} />
        <SmallStat title="Total Chunks" value={loading ? "—" : totalChunks} />
        <SmallStat title="Last Upload" value={lastIngest ? new Date(lastIngest).toLocaleString() : "—"} />
      </div>

      <div className="card mb-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Ingestion Sparkline (last sources)</h3>
          <div className="text-sm text-gray-500">Shows recent ingestions (pre-aggregated)</div>
        </div>
        <div style={{ height: 120 }} className="mt-3">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparkData}>
              <Line type="monotone" dataKey="c" stroke="#06b6d4" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="card">
          <h4 className="font-semibold">Process server-side test file</h4>
          <div className="text-sm text-gray-600 mb-2">Select a file from the backend test files directory and process it server-side (no upload from client).</div>
          <div className="flex items-center gap-2">
            <select className="border p-2 rounded flex-1" value={selectedFile} onChange={(e) => setSelectedFile(e.target.value)}>
              <option value="">-- select file --</option>
              {testFiles.map((f) => <option key={f.name} value={f.name}>{f.name} ({(f.size/1024).toFixed(1)} KB)</option>)}
            </select>
            <button className="px-3 py-1 bg-primary text-white rounded" onClick={handleProcessFile}>Process</button>
          </div>
          <div className="mt-2 text-sm">
            {processingStatus && <div className={processingStatus.status === "error" ? "text-red-600" : "text-green-600"}>{processingStatus.msg}</div>}
          </div>
        </div>

        <div className="card">
          <h4 className="font-semibold">Upload local file</h4>
          <div className="text-sm text-gray-600 mb-2">Choose a file from your machine and upload it to the backend /upload endpoint.</div>
          <input type="file" onChange={handleUploadLocal} className="mb-2" />
          <div className="text-sm">
            {uploading && <div className="text-blue-600">Uploading...</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
