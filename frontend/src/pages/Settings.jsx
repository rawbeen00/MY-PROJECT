import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Save } from "lucide-react";
import api from "@/lib/api";

export default function Settings() {
  const [s, setS] = useState(null);

  useEffect(() => { api.get("/settings").then(({ data }) => setS(data)); }, []);

  if (!s) return <div className="text-slate-500">Loading…</div>;

  const set = (k, v) => setS({ ...s, [k]: v });

  const save = async () => {
    await api.put("/settings", s);
    toast.success("Settings saved");
  };

  const fields = [
    ["company_name", "Company Name"],
    ["tagline", "Tagline"],
    ["trn", "TRN"],
    ["address", "Address", true],
    ["email", "Email"],
    ["phone", "Phone"],
    ["website", "Website"],
    ["bank_name", "Bank Name"],
    ["account_title", "Account Title"],
    ["account_number", "Account Number"],
    ["iban", "IBAN"],
    ["currency", "Currency"],
    ["branch", "Branch"],
    ["swift_code", "Swift Code"],
    ["default_vat", "Default VAT %"],
    ["invoice_prefix", "Invoice Prefix"],
  ];

  return (
    <div className="space-y-5 af-fade">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500 mt-0.5">Company & invoice template configuration</p>
      </div>
      <div className="af-card">
        <div className="af-section-header">Company & Bank Details</div>
        <div className="af-card-body grid grid-cols-2 gap-4">
          {fields.map(([k, label, full]) => (
            <div key={k} className={full ? "col-span-2" : ""}>
              <label className="af-label">{label}</label>
              <input className="af-input" value={s[k] ?? ""} onChange={(e) => set(k, e.target.value)} />
            </div>
          ))}
          <div className="col-span-2">
            <label className="af-label">Additional Websites (one per line)</label>
            <textarea
              className="af-input min-h-[80px]"
              value={(s.extra_websites || []).join("\n")}
              onChange={(e) => set("extra_websites", e.target.value.split("\n").filter(Boolean))}
            />
          </div>
        </div>
      </div>
      <button onClick={save} data-testid="settings-save-btn" className="af-btn af-btn-primary"><Save size={16} /> Save Settings</button>
    </div>
  );
}
