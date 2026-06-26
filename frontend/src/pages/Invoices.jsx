import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Search, Printer, Copy, Trash2, Edit3, Plus } from "lucide-react";
import api, { API_BASE } from "@/lib/api";
import { fmtAED } from "@/lib/calc";

export default function Invoices() {
  const [list, setList] = useState([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    const { data } = await api.get(`/invoices?q=${encodeURIComponent(q)}&limit=100`);
    setList(data.items);
    setLoading(false);
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);
  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
    // eslint-disable-next-line
  }, [q]);

  const openPdf = (inv) => {
    const token = localStorage.getItem("af_token") || "";
    window.open(`${API_BASE}/invoices/${inv.id}/pdf?token=${encodeURIComponent(token)}`, "_blank");
  };

  const duplicate = async (inv) => {
    const { data } = await api.post("/invoices", {
      ...inv, invoice_no: null, id: undefined, created_at: undefined,
    });
    toast.success(`Duplicated as ${data.invoice_no}`);
    navigate(`/invoice/${data.id}`);
  };

  const remove = async (inv) => {
    if (!window.confirm(`Delete invoice ${inv.invoice_no}?`)) return;
    await api.delete(`/invoices/${inv.id}`);
    toast.success("Deleted");
    load();
  };

  return (
    <div className="space-y-5 af-fade">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Invoice History</h1>
          <p className="text-sm text-slate-500 mt-0.5">{list.length} invoices</p>
        </div>
        <Link to="/invoice/new" className="af-btn af-btn-primary" data-testid="invoices-new-btn"><Plus size={16} /> New Invoice</Link>
      </div>

      <div className="af-card p-4">
        <div className="relative max-w-md">
          <Search size={14} className="absolute left-3 top-3 text-slate-400" />
          <input data-testid="invoices-search" className="af-input pl-9" placeholder="Search by invoice no, TRN, company…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      <div className="af-card overflow-hidden">
        <table className="af-table">
          <thead>
            <tr>
              <th>Invoice No</th>
              <th>Date</th>
              <th>Company</th>
              <th>TRN</th>
              <th className="text-right">Net Total</th>
              <th className="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={6} className="text-center py-8 text-slate-400">Loading…</td></tr>}
            {!loading && list.length === 0 && <tr><td colSpan={6} className="text-center py-8 text-slate-400">No invoices found</td></tr>}
            {list.map((inv) => (
              <tr key={inv.id} data-testid={`invoice-row-${inv.invoice_no}`}>
                <td className="font-semibold text-slate-800">{inv.invoice_no}</td>
                <td>{inv.date}</td>
                <td>{inv.customer?.company_name || "—"}</td>
                <td className="text-slate-500">{inv.customer?.customer_trn || "—"}</td>
                <td className="text-right font-bold text-orange-600">AED {fmtAED(inv.net_total)}</td>
                <td>
                  <div className="flex gap-1 justify-end">
                    <button onClick={() => navigate(`/invoice/${inv.id}`)} className="af-btn af-btn-ghost py-1.5 px-2.5" title="Edit"><Edit3 size={14} /></button>
                    <button onClick={() => openPdf(inv)} className="af-btn af-btn-ghost py-1.5 px-2.5" title="PDF"><Printer size={14} /></button>
                    <button onClick={() => duplicate(inv)} className="af-btn af-btn-ghost py-1.5 px-2.5" title="Duplicate"><Copy size={14} /></button>
                    <button onClick={() => remove(inv)} className="af-btn af-btn-danger-ghost py-1.5 px-2.5" title="Delete"><Trash2 size={14} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
