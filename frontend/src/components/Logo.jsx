import { useEffect, useState } from "react";
import api from "@/lib/api";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export function AnsaryLogo({ size = 56, className = "", showText = true }) {
  const [logoUrl, setLogoUrl] = useState("");

  useEffect(() => {
    let cancelled = false;
    api.get("/settings/public").then(({ data }) => {
      if (!cancelled && data.logo_url) setLogoUrl(data.logo_url);
    }).catch(() => {});
    return () => { cancelled = true; };
  }, []);

  if (logoUrl) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <div className="bg-white rounded-lg p-2 shadow-sm" style={{ display: "inline-flex" }}>
          <img
            src={`${BACKEND_URL}${logoUrl}`}
            alt="Ansary Furniture"
            style={{ height: size, width: "auto", objectFit: "contain" }}
          />
        </div>
      </div>
    );
  }

  // Fallback vector logo
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <svg width={size} height={size} viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
        <polygon points="6,40 32,12 58,40 53,40 32,21 11,40" fill="#111827" />
        <rect x="24" y="32" width="16" height="14" fill="#F58220" />
        <line x1="32" y1="32" x2="32" y2="46" stroke="white" strokeWidth="2" />
        <line x1="24" y1="39" x2="40" y2="39" stroke="white" strokeWidth="2" />
      </svg>
      {showText && (
        <div className="leading-tight">
          <div className="font-bold text-[15px] text-[#F58220] tracking-wide">ANSARY FURNITURE</div>
          <div className="text-[9px] text-slate-500 tracking-widest">LET'S DECORATE YOUR HOME</div>
        </div>
      )}
    </div>
  );
}
