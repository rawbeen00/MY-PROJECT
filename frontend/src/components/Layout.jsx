import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { LayoutDashboard, FileText, Users, Settings as SettingsIcon, FilePlus2, LogOut } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { AnsaryLogo } from "@/components/Logo";

const items = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, tid: "nav-dashboard" },
  { to: "/invoice/new", label: "New Invoice", icon: FilePlus2, tid: "nav-new-invoice" },
  { to: "/invoices", label: "Invoices", icon: FileText, tid: "nav-invoices" },
  { to: "/customers", label: "Customers", icon: Users, tid: "nav-customers" },
  { to: "/settings", label: "Settings", icon: SettingsIcon, tid: "nav-settings" },
];

export default function Layout() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex bg-[#f6f7fb]">
      <aside className="w-[240px] bg-[#1f2a44] text-white flex-shrink-0 flex flex-col">
        <div className="px-5 py-5 border-b border-white/10">
          <AnsaryLogo size={42} />
          <div className="text-[10px] text-slate-400 mt-2 tracking-wider">INVOICE & CUSTOMER SYSTEM</div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {items.map((it) => (
            <NavLink key={it.to} to={it.to} data-testid={it.tid} className={({ isActive }) => `af-sidebar-link ${isActive ? "active" : ""}`}>
              <it.icon size={18} />
              <span>{it.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-white/10">
          <div className="px-3 pb-2 text-xs text-slate-400">{user?.email}</div>
          <button
            data-testid="logout-button"
            onClick={async () => { await logout(); navigate("/login"); }}
            className="af-sidebar-link w-full"
          >
            <LogOut size={18} /> Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-x-hidden">
        <div className="max-w-[1400px] mx-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
