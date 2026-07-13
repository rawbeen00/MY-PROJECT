import { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";
import { AnsaryLogo } from "@/components/Logo";

export default function Login() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState("admin@ansaryfurniture.com");
  const [password, setPassword] = useState("Admin@123");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  if (user) return <Navigate to="/dashboard" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email.trim().toLowerCase(), password);
      toast.success("Welcome back");
      navigate("/dashboard");
    } catch (err) {
      const d = err.response?.data?.detail;
      toast.error(typeof d === "string" ? d : "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: "linear-gradient(135deg, #1f2a44 0%, #2c3a5f 100%)" }}>
      <div className="w-full max-w-md af-card af-fade">
        <div className="p-8">
          <div className="flex justify-center mb-6"><AnsaryLogo size={56} /></div>
          <h1 className="text-xl font-bold text-slate-900 text-center mb-1">Welcome back</h1>
          <p className="text-sm text-slate-500 text-center mb-6">Sign in to manage invoices & customers</p>
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="af-label">Email</label>
              <input data-testid="login-email" className="af-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <label className="af-label">Password</label>
              <input data-testid="login-password" className="af-input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <button data-testid="login-submit" type="submit" disabled={loading} className="af-btn af-btn-primary w-full justify-center">
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
          <div className="mt-6 text-xs text-slate-400 text-center">
              Enter your account credentials to continue.
          </div>
        </div>
      </div>
    </div>
  );
}
