// src/components/ConfirmModal.jsx
import React, { useEffect, useRef } from "react";

export default function ConfirmModal({ open, title, description, children, onClose }) {
  const ref = useRef(null);
  useEffect(() => {
    if (open) ref.current?.focus();
  }, [open]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="bg-white rounded-2xl p-6 z-10 w-full max-w-lg">
        <h2 id="modal-title" className="text-lg font-semibold">{title}</h2>
        <p className="text-sm text-gray-600 mt-2">{description}</p>
        <div className="mt-4">
          {children}
        </div>
        <div className="mt-4 text-right">
          <button ref={ref} onClick={onClose} className="px-3 py-1 rounded border">Close</button>
        </div>
      </div>
    </div>
  );
}
