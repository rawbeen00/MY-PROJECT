import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Plus, Edit3, Trash2, Search, X, Save } from "lucide-react";
import api from "@/lib/api";

const empty = { customer_trn: "", company_name: "", contact_person: "", phone: "", email: "", address: "" };

export default function Customers() {
  const [list, setList] = useState([]);
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(empty);

  const load = async () => {
    const { data } = await api.get(`/customers?q=${encodeURIComponent(q)}&limit=200`);
    setList(data.items);
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t); /* eslint-disable-next-line */ }, [q]);

  const startNew = () => { setEditing({ new: true }); setForm(empty); };
  const startEdit = (c) => { setEditing(c); setForm(c); };
  const cancel = () => { setEditing(null); setForm(empty); };

  const save = async () => {
    try {
      if (editing.new) {
        const { data } = await api.post("/customers", form);
        if (data.existing) toast.info("Existing TRN — opened existing customer");
        else toast.success("Customer added");
      } else {
        await api.put(`/customers/${editing.id}`, form);
        toast.success("Customer updated");
      }
      cancel(); load();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed");
    }
  };

  const remove = async (c) => {
    if (!window.confirm(`Delete ${c.company_name || c.customer_trn}?`)) return;
    await api.delete(`/customers/${c.id}`);
    toast.success("Deleted");
    load();
  };

  return (
    <div className="space-y-5 af-fade">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Customers</h1>
          <p className="text-sm text-slate-500 mt-0.5">{list.length} records</p>
        </div>
        <button data-testid="add-customer-btn" onClick={startNew} className="af-btn af-btn-primary"><Plus size={16} /> Add Customer</button>
      </div>

      <div className="af-card p-4">
        <div className="relative max-w-md">
          <Search size={14} className="absolute left-3 top-3 text-slate-400" />
          <input data-testid="customers-search" className="af-input pl-9" placeholder="Search by TRN, company, contact, phone…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      <div className="af-card overflow-hidden">
        <table className="af-table">
          <thead>
            <tr>
              <th>TRN</th>
              <th>Company</th>
              <th>Contact</th>
              <th>Phone</th>
              <th>Email</th>
              <th className="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {list.length === 0 && <tr><td colSpan={6} className="text-center py-8 text-slate-400">No customers</td></tr>}
            {list.map((c) => (
              <tr key={c.id}>
                <td className="font-mono text-xs">{c.customer_trn}</td>
                <td className="font-semibold text-slate-800">{c.company_name}</td>
                <td>{c.contact_person}</td>
                <td>{c.phone}</td>
                <td className="text-slate-500">{c.email}</td>
                <td>
                  <div className="flex gap-1 justify-end">
                    <button onClick={() => startEdit(c)} className="af-btn af-btn-ghost py-1.5 px-2.5"><Edit3 size={14} /></button>
                    <button onClick={() => remove(c)} className="af-btn af-btn-danger-ghost py-1.5 px-2.5"><Trash2 size={14} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && (
        <div className="fixed inset-0 bg-slate-900/50 z-50 flex items-center justify-center p-4">
          <div className="af-card w-full max-w-2xl af-fade">
            <div className="af-section-header justify-between">
              <span>{editing.new ? "Add Customer" : "Edit Customer"}</span>
              <button onClick={cancel} className="text-white"><X size={18} /></button>
            </div>
            <div className="af-card-body grid grid-cols-2 gap-4">
              {[
                ["customer_trn", "Customer TRN"],
                ["company_name", "Company Name"],
                ["contact_person", "Contact Person"],
                ["phone", "Phone"],
                ["email", "Email"],
                ["address", "Address", true],
              ].map(([k, label, full]) => (
                <div key={k} className={full ? "col-span-2" : ""}>
                  <label className="af-label">{label}</label>
                  <input className="af-input" value={form[k] || ""} onChange={(e) => setForm({ ...form, [k]: e.target.value })} />
                </div>
              ))}
              <div className="col-span-2 flex gap-2 justify-end pt-2">
                <button onClick={cancel} className="af-btn af-btn-ghost">Cancel</button>
                <button onClick={save} className="af-btn af-btn-primary"><Save size={14} /> Save</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
