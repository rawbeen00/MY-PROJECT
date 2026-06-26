import { useRef, useState } from "react";
import { toast } from "sonner";
import { Upload, Trash2, Image as ImageIcon } from "lucide-react";
import api from "@/lib/api";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function AssetUploader({ kind, label, value, onChange }) {
  const fileRef = useRef(null);
  const [busy, setBusy] = useState(false);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!/^image\/(png|jpe?g|webp)$/i.test(file.type)) {
      toast.error("Only PNG / JPG / WEBP images are allowed");
      return;
    }
    const fd = new FormData();
    fd.append("file", file);
    setBusy(true);
    try {
      const { data } = await api.post(`/settings/upload/${kind}`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onChange(`${data.url}?t=${Date.now()}`);
      toast.success(`${label} uploaded`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Upload failed");
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleRemove = async () => {
    if (!window.confirm(`Remove ${label}?`)) return;
    setBusy(true);
    try {
      await api.delete(`/settings/upload/${kind}`);
      onChange("");
      toast.success(`${label} removed`);
    } catch (err) {
      toast.error("Failed to remove");
    } finally {
      setBusy(false);
    }
  };

  const src = value ? `${BACKEND_URL}${value.split("?")[0]}?t=${Date.now()}` : null;

  return (
    <div className="af-card p-4" data-testid={`asset-${kind}`}>
      <div className="flex items-center justify-between mb-3">
        <label className="af-label !mb-0">{label}</label>
        <div className="flex gap-1.5">
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="af-btn af-btn-ghost py-1.5 px-3 text-xs"
            disabled={busy}
            data-testid={`upload-${kind}-btn`}
          >
            <Upload size={13} /> {value ? "Replace" : "Upload"}
          </button>
          {value && (
            <button
              type="button"
              onClick={handleRemove}
              className="af-btn af-btn-danger-ghost py-1.5 px-3 text-xs"
              disabled={busy}
              data-testid={`remove-${kind}-btn`}
            >
              <Trash2 size={13} />
            </button>
          )}
        </div>
      </div>
      <input
        ref={fileRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        className="hidden"
        onChange={handleUpload}
        data-testid={`file-${kind}-input`}
      />
      <div className="h-32 rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 flex items-center justify-center overflow-hidden">
        {src ? (
          <img src={src} alt={label} className="max-h-full max-w-full object-contain p-2" />
        ) : (
          <div className="text-center text-slate-400">
            <ImageIcon size={28} className="mx-auto mb-1 opacity-60" />
            <div className="text-xs">No {label.toLowerCase()} uploaded</div>
          </div>
        )}
      </div>
      <p className="text-[11px] text-slate-400 mt-2">PNG, JPG or WEBP. Recommended transparent background.</p>
    </div>
  );
}
