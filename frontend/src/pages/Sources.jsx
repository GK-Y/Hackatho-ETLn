// src/pages/Sources.jsx
import React, { useEffect, useState } from "react";
import { getSources, postBackup, deleteDataset } from "../api/client";
import ConfirmModal from "../components/ConfirmModal";

export default function Sources() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [backupCmd, setBackupCmd] = useState(null);
  const [modal, setModal] = useState({ open: false, source: null, step: "start" });
  const [typedConfirm, setTypedConfirm] = useState("");

  useEffect(() => {
    load();
  }, []);

  async function load() {
    setLoading(true);
    const res = await getSources();
    if (!res.error) setSources(res.data || []);
    setLoading(false);
  }

  async function handleBackup(sourceId) {
    setBackupCmd(null);
    const res = await postBackup(sourceId);
    if (!res.error && res.data) {
      setBackupCmd(res.data);
      setModal({ open: true, source: sourceId, step: "backed" });
    } else {
      setBackupCmd({ error: res.error || "Failed to get backup command" });
    }
  }

  async function handleDelete(sourceId) {
    // require typed confirm equals sourceId
    if (typedConfirm !== sourceId) return alert("Type the source_id to confirm deletion.");
    const res = await deleteDataset(sourceId, 1);
    if (!res.error) {
      alert("Delete success. Refreshing sources.");
      await load();
      setModal({ open: false, source: null, step: "start" });
      setTypedConfirm("");
    } else {
      alert("Delete failed: " + JSON.stringify(res.error));
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Sources</h2>
      </div>

      <div className="card">
        {loading ? (
          <div className="skeleton h-24" />
        ) : (
          <table className="w-full text-left">
            <thead>
              <tr className="text-sm text-gray-500">
                <th className="p-2">Source ID</th>
                <th>Last Ingest</th>
                <th>Records</th>
                <th>Schema v</th>
                <th>Chunks</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sources.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-4 text-sm text-gray-500">No sources found</td>
                </tr>
              )}
              {sources.map((s) => (
                <tr key={s.source_id} className="border-t">
                  <td className="p-2 font-mono">{s.source_id}</td>
                  <td>{s.last_ingest ? new Date(s.last_ingest).toLocaleString() : "—"}</td>
                  <td>{s.record_count}</td>
                  <td>{s.schema_version}</td>
                  <td>{s.chunks}</td>
                  <td className="space-x-2">
                    <a className="text-sm px-2 py-1 border rounded" href={`#/records/${s.source_id}`}>View Records</a>
                    <a className="text-sm px-2 py-1 border rounded" href={`#/schema/${s.source_id}`}>Schema</a>
                    <a className="text-sm px-2 py-1 bg-primary text-white rounded" href={`#/visualize/${s.source_id}`}>Visualize</a>
                    <button onClick={() => handleBackup(s.source_id)} className="text-sm px-2 py-1 border rounded">Backup</button>
                    <button onClick={() => setModal({ open: true, source: s.source_id, step: "start" })} className="text-sm px-2 py-1 border rounded">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <ConfirmModal
        open={modal.open}
        title={modal.step === "start" ? "Delete dataset — Backup required" : "Backup command"}
        description={modal.step === "start" ? `You are about to delete dataset ${modal.source}. Backup is required before deleting.` : "Copy and run the mongodump command locally (PowerShell). After running it, type the source_id exactly and press Confirm to enable deletion."}
        onClose={() => { setModal({ open: false, source: null, step: "start" }); setTypedConfirm(""); }}
      >
        {modal.step === "start" ? (
          <div>
            <div className="mb-2">
              <button onClick={() => handleBackup(modal.source)} className="px-3 py-1 bg-primary text-white rounded">Generate Backup Command</button>
            </div>
            <div className="text-sm text-gray-500">You must run the backup locally before deletion. The Delete button will ask you to type the source_id to confirm.</div>
          </div>
        ) : (
          <div>
            <div className="bg-gray-100 p-3 rounded text-xs mb-2 overflow-auto max-h-36">
              <code>{backupCmd?.data || backupCmd || "No command returned"}</code>
            </div>
            <div className="text-sm mb-2">After running the command on the machine hosting MongoDB, type the source_id below to enable deletion.</div>
            <input placeholder="Type source_id to confirm" value={typedConfirm} onChange={(e) => setTypedConfirm(e.target.value)} className="border p-2 rounded w-full mb-2" />
            <div className="flex justify-end gap-2">
              <button onClick={() => setModal({ open: true, source: modal.source, step: "backed" })} className="px-3 py-1 border rounded">Refresh</button>
              <button disabled={typedConfirm !== modal.source} onClick={() => handleDelete(modal.source)} className={`px-3 py-1 rounded ${typedConfirm === modal.source ? "bg-red-600 text-white" : "bg-gray-200"}`}>Confirm Delete</button>
            </div>
          </div>
        )}
      </ConfirmModal>
    </div>
  );
}
