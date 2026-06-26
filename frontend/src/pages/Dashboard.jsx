import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { TrendingUp, FileText, Users, Wallet, Calendar, Percent } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";
import api from "@/lib/api";
import { fmtAED } from "@/lib/calc";

const Stat = ({ icon: Icon, label, value, accent = "orange", tid }) => (
  <div className="af-card p-5" data-testid={tid}>
    <div className="flex items-center gap-3">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${accent === "orange" ? "bg-orange-100 text-orange-600" : accent === "navy" ? "bg-slate-900 text-white" : "bg-emerald-100 text-emerald-600"}`}>
        <Icon size={20} />
      </div>
      <div>
        <div className="text-xs text-slate-500 uppercase tracking-wide font-semibold">{label}</div>
        <div className="text-xl font-bold text-slate-900 mt-0.5">{value}</div>
      </div>
    </div>
  </div>
);

export default function Dashboard() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.get("/dashboard/stats").then(({ data }) => setStats(data));
  }, []);

  if (!stats) return <div className="text-slate-500">Loading…</div>;

  return (
    <div className="space-y-6 af-fade">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">Overview of your invoicing activity</p>
        </div>
        <Link to="/invoice/new" className="af-btn af-btn-primary" data-testid="dashboard-new-invoice">
          <FileText size={16} /> New Invoice
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat tid="stat-today-invoices" icon={Calendar} label="Today's Invoices" value={stats.today_invoices} />
        <Stat tid="stat-today-revenue" icon={TrendingUp} label="Today's Revenue" value={`AED ${fmtAED(stats.today_revenue)}`} accent="navy" />
        <Stat tid="stat-monthly-revenue" icon={Wallet} label="Monthly Revenue" value={`AED ${fmtAED(stats.monthly_revenue)}`} accent="emerald" />
        <Stat tid="stat-vat" icon={Percent} label="VAT Collected (mo)" value={`AED ${fmtAED(stats.vat_collected)}`} />
        <Stat tid="stat-total-invoices" icon={FileText} label="Total Invoices" value={stats.total_invoices} accent="navy" />
        <Stat tid="stat-total-customers" icon={Users} label="Total Customers" value={stats.total_customers} />
        <Stat tid="stat-monthly-invoices" icon={FileText} label="Invoices This Month" value={stats.monthly_invoices} accent="emerald" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="af-card lg:col-span-2 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Monthly Revenue (last 6 months)</h2>
          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={stats.trend}>
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip />
                <Bar dataKey="revenue" fill="#F58220" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="af-card p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Invoices Count</h2>
          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <LineChart data={stats.trend}>
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#1f2a44" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="af-card p-5">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">Top Customers</h2>
        {stats.top_customers.length === 0 ? (
          <div className="text-slate-400 text-sm">No invoices yet.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="text-xs uppercase tracking-wider text-slate-500">
              <tr><th className="text-left py-2">Customer</th><th className="text-right">Invoices</th><th className="text-right">Total Revenue</th></tr>
            </thead>
            <tbody>
              {stats.top_customers.map((t, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="py-2 font-medium text-slate-800">{t.name}</td>
                  <td className="text-right">{t.count}</td>
                  <td className="text-right text-orange-600 font-bold">AED {fmtAED(t.total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
