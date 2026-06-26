import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { FileText, User, ListPlus, Save, Printer, RotateCcw, Trash2, Copy, Plus, Search, FileDigit } from "lucide-react";
import api, { API_BASE } from "@/lib/api";
import { amountToWords, fmtAED, calcTotals, recalcRow } from "@/lib/calc";

const emptyRow = () => ({
  description: "", qty: "", unit: "", unit_price: "", vat_percent: 5, total_excl: 0, total_incl: 0,
});

const emptyCustomer = {
  customer_trn: "", contact_person: "", company_name: "",
  address: "", phone: "", email: "",
};

export default function InvoiceEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [invoiceNo, setInvoiceNo] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [doNo, setDoNo] = useState("");
  const [lpoNo, setLpoNo] = useState("");
  const [customer, setCustomer] = useState(emptyCustomer);
  const [items, setItems] = useState([emptyRow()]);
  const [discount, setDiscount] = useState(0);
  const [notes, setNotes] = useState("");
  const [terms, setTerms] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSug, setShowSug] = useState(false);
  const [searchQ, setSearchQ] = useState("");
  const [searchRes, setSearchRes] = useState([]);
  const [saving, setSaving] = useState(false);
  const [savedId, setSavedId] = useState(null);
  const trnDebounce = useRef(null);
  const searchDebounce = useRef(null);

  const totals = useMemo(() => calcTotals(items, discount), [items, discount]);
  const amountWords = useMemo(() => amountToWords(totals.net_total), [totals.net_total]);

  useEffect(() => {
    if (id) {
      api.get(`/invoices/${id}`).then(({ data }) => {
        setInvoiceNo(data.invoice_no);
        setDate(data.date);
        setDoNo(data.do_no || "");
        setLpoNo(data.lpo_no || "");
        setCustomer({ ...emptyCustomer, ...data.customer });
        setItems(data.items?.length ? data.items : [emptyRow()]);
        setDiscount(data.discount || 0);
        setNotes(data.notes || "");
        setTerms(data.terms || "");
        setSavedId(data.id);
      }).catch(() => toast.error("Failed to load invoice"));
    } else {
      api.get("/invoices/next-number").then(({ data }) => setInvoiceNo(data.invoice_no)).catch(() => {});
    }
  }, [id]);

  // TRN autofill + suggestions
  const onTrnChange = (v) => {
    setCustomer((c) => ({ ...c, customer_trn: v }));
    if (trnDebounce.current) clearTimeout(trnDebounce.current);
    if (!v) { setSuggestions([]); setShowSug(false); return; }
    trnDebounce.current = setTimeout(async () => {
      try {
        const { data } = await api.get(`/customers/search?q=${encodeURIComponent(v)}`);
        setSuggestions(data);
        setShowSug(data.length > 0);
        // Exact TRN match -> autofill immediately
        const exact = data.find((d) => d.customer_trn === v);
        if (exact) fillCustomer(exact);
      } catch {}
    }, 220);
  };

  const fillCustomer = (c) => {
    setCustomer({
      customer_trn: c.customer_trn || "",
      contact_person: c.contact_person || "",
      company_name: c.company_name || "",
      address: c.address || "",
      phone: c.phone || "",
      email: c.email || "",
    });
    setShowSug(false);
  };

  // Search records (right sidebar)
  useEffect(() => {
    if (searchDebounce.current) clearTimeout(searchDebounce.current);
    if (!searchQ) { setSearchRes([]); return; }
    searchDebounce.current = setTimeout(async () => {
      const { data } = await api.get(`/invoices?q=${encodeURIComponent(searchQ)}&limit=8`);
      setSearchRes(data.items || []);
    }, 250);
  }, [searchQ]);

  // Row helpers
  const updateRow = (idx, patch) => {
    setItems((rows) => rows.map((r, i) => (i === idx ? recalcRow({ ...r, ...patch }) : r)));
  };
  const addRow = () => setItems((r) => [...r, emptyRow()]);
  const removeRow = (idx) => setItems((r) => (r.length === 1 ? [emptyRow()] : r.filter((_, i) => i !== idx)));
  const duplicateRow = (idx) => setItems((r) => {
    const nr = [...r];
    nr.splice(idx + 1, 0, { ...r[idx] });
    return nr;
  });

  const buildPayload = () => ({
    invoice_no: invoiceNo || null,
    date,
    do_no: doNo,
    lpo_no: lpoNo,
    customer,
    items: items.map(recalcRow),
    gross_total: totals.gross_total,
    discount: parseFloat(discount) || 0,
    vat_total: totals.vat_total,
    net_total: totals.net_total,
    amount_words: amountWords,
    notes,
    terms,
  });

  const save = async () => {
    if (!customer.company_name && !customer.customer_trn) {
      toast.error("Please enter Customer TRN or Company Name");
      return;
    }
    setSaving(true);
    try {
      if (savedId) {
        const { data } = await api.put(`/invoices/${savedId}`, buildPayload());
        toast.success(`Invoice ${data.invoice_no} updated`);
      } else {
        const { data } = await api.post("/invoices", buildPayload());
        setSavedId(data.id);
        setInvoiceNo(data.invoice_no);
        toast.success(`Invoice ${data.invoice_no} saved`);
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const printPdf = async () => {
    try {
      if (savedId) {
        const token = localStorage.getItem("af_token");
        window.open(`${API_BASE}/invoices/${savedId}/pdf?token=${encodeURIComponent(token || "")}`, "_blank");
      } else {
        // Preview without saving
        const res = await api.post("/invoices/preview-pdf", buildPayload(), { responseType: "blob" });
        const url = URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
        window.open(url, "_blank");
      }
    } catch {
      toast.error("PDF generation failed");
    }
  };

  const clearForm = () => {
    setCustomer(emptyCustomer);
    setItems([emptyRow()]);
    setDiscount(0); setDoNo(""); setLpoNo(""); setNotes(""); setTerms("");
    setSavedId(null);
    api.get("/invoices/next-number").then(({ data }) => setInvoiceNo(data.invoice_no));
    if (id) navigate("/invoice/new");
  };

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); save(); }
      if ((e.ctrlKey || e.metaKey) && e.key === "p") { e.preventDefault(); printPdf(); }
      if ((e.ctrlKey || e.metaKey) && e.key === "n") { e.preventDefault(); clearForm(); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  return (
    <div className="grid grid-cols-[1fr_320px] gap-6 af-fade">
      <div className="space-y-5">
        {/* Invoice Details */}
        <div className="af-card">
          <div className="af-section-header"><FileText size={16} /> Invoice Details</div>
          <div className="af-card-body grid grid-cols-2 gap-5">
            <div>
              <label className="af-label">Invoice No.</label>
              <input data-testid="invoice-no-input" className="af-input" value={invoiceNo} onChange={(e) => setInvoiceNo(e.target.value)} placeholder="AF-000001" />
            </div>
            <div>
              <label className="af-label">Date</label>
              <input data-testid="invoice-date-input" type="date" className="af-input" value={date} onChange={(e) => setDate(e.target.value)} />
            </div>
            <div>
              <label className="af-label">D.O. No.</label>
              <input data-testid="invoice-do-input" className="af-input" value={doNo} onChange={(e) => setDoNo(e.target.value)} placeholder="Optional" />
            </div>
            <div>
              <label className="af-label">L.P.O. No.</label>
              <input data-testid="invoice-lpo-input" className="af-input" value={lpoNo} onChange={(e) => setLpoNo(e.target.value)} placeholder="e.g. CK-LPO-9782" />
            </div>
          </div>
        </div>

        {/* Customer Details */}
        <div className="af-card">
          <div className="af-section-header"><User size={16} /> Customer Details</div>
          <div className="af-card-body space-y-4">
            <div className="relative">
              <label className="af-label">Customer TRN <span className="text-red-500">*</span></label>
              <input
                data-testid="customer-trn-input"
                className="af-input"
                value={customer.customer_trn}
                onChange={(e) => onTrnChange(e.target.value)}
                onFocus={() => suggestions.length && setShowSug(true)}
                onBlur={() => setTimeout(() => setShowSug(false), 150)}
                placeholder="Type TRN — auto-fills known customer…"
              />
              {showSug && suggestions.length > 0 && (
                <div data-testid="trn-suggestions" className="absolute z-30 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-64 overflow-auto">
                  {suggestions.map((s) => (
                    <button
                      key={s.id}
                      data-testid={`trn-suggestion-${s.id}`}
                      onMouseDown={(e) => { e.preventDefault(); fillCustomer(s); }}
                      className="w-full text-left px-3 py-2 hover:bg-orange-50 border-b border-slate-100 last:border-0"
                    >
                      <div className="text-sm font-semibold text-slate-800">{s.company_name || "—"}</div>
                      <div className="text-xs text-slate-500">TRN {s.customer_trn} {s.phone && `· ${s.phone}`}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div className="grid grid-cols-2 gap-5">
              <div>
                <label className="af-label">To M/s (Contact)</label>
                <input data-testid="customer-contact-input" className="af-input" value={customer.contact_person}
                  onChange={(e) => setCustomer({ ...customer, contact_person: e.target.value })} placeholder="Contact name" />
              </div>
              <div>
                <label className="af-label">Company Name</label>
                <input data-testid="customer-company-input" className="af-input" value={customer.company_name}
                  onChange={(e) => setCustomer({ ...customer, company_name: e.target.value })} placeholder="Company name" />
              </div>
              <div className="col-span-2">
                <label className="af-label">Address</label>
                <input data-testid="customer-address-input" className="af-input" value={customer.address}
                  onChange={(e) => setCustomer({ ...customer, address: e.target.value })} placeholder="Full address" />
              </div>
              <div>
                <label className="af-label">Phone No.</label>
                <input data-testid="customer-phone-input" className="af-input" value={customer.phone}
                  onChange={(e) => setCustomer({ ...customer, phone: e.target.value })} placeholder="+971 …" />
              </div>
              <div>
                <label className="af-label">E-mail</label>
                <input data-testid="customer-email-input" className="af-input" value={customer.email}
                  onChange={(e) => setCustomer({ ...customer, email: e.target.value })} placeholder="email@company.com" />
              </div>
            </div>
          </div>
        </div>

        {/* Line Items */}
        <div className="af-card">
          <div className="af-section-header"><ListPlus size={16} /> Line Items</div>
          <div className="af-card-body">
            <div className="overflow-x-auto">
              <table className="af-table">
                <thead>
                  <tr>
                    <th className="w-[40px]">#</th>
                    <th>Description</th>
                    <th className="w-[80px]">Qty</th>
                    <th className="w-[80px]">Unit</th>
                    <th className="w-[110px]">Unit Price (AED)</th>
                    <th className="w-[80px]">VAT %</th>
                    <th className="w-[110px] text-right">Total Excl.</th>
                    <th className="w-[110px] text-right">Total Incl.</th>
                    <th className="w-[110px]"></th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((row, i) => (
                    <tr key={i}>
                      <td className="text-center text-slate-500">{i + 1}</td>
                      <td><input data-testid={`row-desc-${i}`} className="af-input" value={row.description} onChange={(e) => updateRow(i, { description: e.target.value })} placeholder="Item description" /></td>
                      <td><input data-testid={`row-qty-${i}`} className="af-input" type="number" min="0" step="any" value={row.qty} onChange={(e) => updateRow(i, { qty: e.target.value })} /></td>
                      <td><input data-testid={`row-unit-${i}`} className="af-input" value={row.unit} onChange={(e) => updateRow(i, { unit: e.target.value })} placeholder="PCS" /></td>
                      <td><input data-testid={`row-price-${i}`} className="af-input" type="number" min="0" step="any" value={row.unit_price} onChange={(e) => updateRow(i, { unit_price: e.target.value })} /></td>
                      <td><input data-testid={`row-vat-${i}`} className="af-input" type="number" min="0" step="any" value={row.vat_percent} onChange={(e) => updateRow(i, { vat_percent: e.target.value })} /></td>
                      <td className="text-right text-slate-700">{fmtAED(row.total_excl)}</td>
                      <td className="text-right font-semibold">{fmtAED(row.total_incl)}</td>
                      <td>
                        <div className="flex gap-1 justify-end">
                          <button data-testid={`row-duplicate-${i}`} onClick={() => duplicateRow(i)} className="p-1.5 rounded hover:bg-slate-100" title="Duplicate"><Copy size={14} /></button>
                          <button data-testid={`row-delete-${i}`} onClick={() => removeRow(i)} className="p-1.5 rounded hover:bg-red-50 text-red-600" title="Delete"><Trash2 size={14} /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button data-testid="add-row-btn" onClick={addRow} className="af-btn af-btn-ghost mt-3"><Plus size={14} /> Add row</button>

            {/* Totals + Amount in words */}
            <div className="grid grid-cols-2 gap-6 mt-6">
              <div>
                <label className="af-label">Amount in Words</label>
                <div data-testid="amount-words" className="px-4 py-3 rounded-lg bg-orange-50 border border-orange-100 text-slate-800 font-medium text-sm tracking-wide">
                  {amountWords}
                </div>
                <label className="af-label mt-4">Discount (AED)</label>
                <input data-testid="discount-input" className="af-input max-w-[200px]" type="number" min="0" step="any" value={discount} onChange={(e) => setDiscount(e.target.value)} />
              </div>
              <div className="space-y-2">
                <div className="af-totals-row"><span>Gross Total</span><span data-testid="gross-total">AED {fmtAED(totals.gross_total)}</span></div>
                <div className="af-totals-row"><span>Discount</span><span>AED {fmtAED(discount)}</span></div>
                <div className="af-totals-row"><span>VAT 5%</span><span data-testid="vat-total">AED {fmtAED(totals.vat_total)}</span></div>
                <div className="af-totals-row highlight"><span>NET TOTAL</span><span data-testid="net-total">AED {fmtAED(totals.net_total)}</span></div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-5 mt-5">
              <div>
                <label className="af-label">Notes (internal)</label>
                <textarea className="af-input min-h-[60px]" value={notes} onChange={(e) => setNotes(e.target.value)} />
              </div>
              <div>
                <label className="af-label">Terms & Conditions</label>
                <textarea className="af-input min-h-[60px]" value={terms} onChange={(e) => setTerms(e.target.value)} />
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-3 pt-1">
          <button data-testid="save-invoice-btn" onClick={save} disabled={saving} className="af-btn af-btn-primary"><Save size={16} /> {saving ? "Saving…" : "Save Invoice"}</button>
          <button data-testid="print-pdf-btn" onClick={printPdf} className="af-btn af-btn-success"><Printer size={16} /> Print / Save PDF</button>
          <button data-testid="clear-form-btn" onClick={clearForm} className="af-btn af-btn-ghost"><RotateCcw size={16} /> Clear</button>
          <div className="ml-auto text-xs text-slate-500 pt-3">⌨ Ctrl+S save · Ctrl+P print · Ctrl+N new</div>
        </div>
      </div>

      {/* Right sidebar: Search Records */}
      <aside className="space-y-4">
        <div className="af-card">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2 text-orange-600 font-semibold text-sm">
            <Search size={16} /> Search Records
          </div>
          <div className="p-3">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-3 text-slate-400" />
              <input
                data-testid="records-search-input"
                value={searchQ}
                onChange={(e) => setSearchQ(e.target.value)}
                placeholder="TRN, name, company, email…"
                className="af-input pl-9"
              />
            </div>
            <div className="mt-3 max-h-[420px] overflow-auto">
              {!searchQ && (
                <div className="text-center text-slate-400 py-10 text-sm">
                  <Search size={26} className="mx-auto mb-2 opacity-50" />
                  Type to search
                </div>
              )}
              {searchQ && searchRes.length === 0 && (
                <div className="text-center text-slate-400 py-6 text-sm">No results</div>
              )}
              {searchRes.map((r) => (
                <button
                  key={r.id}
                  data-testid={`search-result-${r.id}`}
                  onClick={() => navigate(`/invoice/${r.id}`)}
                  className="w-full text-left p-3 rounded-lg hover:bg-orange-50 border-b border-slate-100"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-slate-800 flex items-center gap-1"><FileDigit size={12} /> {r.invoice_no}</span>
                    <span className="text-xs font-bold text-orange-600">AED {fmtAED(r.net_total)}</span>
                  </div>
                  <div className="text-xs text-slate-600 mt-0.5">{r.customer?.company_name || "—"}</div>
                  <div className="text-[11px] text-slate-400">{r.date}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}
