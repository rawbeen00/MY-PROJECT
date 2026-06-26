// Convert AED amount to words: "ONE THOUSAND FIVE HUNDRED TWENTY DIRHAMS ONLY"
const ones = [
  "", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE",
  "TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN",
  "SEVENTEEN", "EIGHTEEN", "NINETEEN",
];
const tens = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"];

function chunk(n) {
  let s = "";
  if (n >= 100) {
    s += ones[Math.floor(n / 100)] + " HUNDRED";
    n %= 100;
    if (n) s += " ";
  }
  if (n >= 20) {
    s += tens[Math.floor(n / 10)];
    if (n % 10) s += " " + ones[n % 10];
  } else if (n > 0) {
    s += ones[n];
  }
  return s.trim();
}

function intToWords(n) {
  if (n === 0) return "ZERO";
  const units = ["", "THOUSAND", "MILLION", "BILLION"];
  let i = 0, out = "";
  while (n > 0) {
    const c = n % 1000;
    if (c) out = (chunk(c) + (units[i] ? " " + units[i] : "") + (out ? " " + out : "")).trim();
    n = Math.floor(n / 1000);
    i++;
  }
  return out.trim();
}

export function amountToWords(amount) {
  if (!amount || isNaN(amount)) return "ZERO DIRHAMS ONLY";
  const rounded = Math.round(parseFloat(amount) * 100) / 100;
  const whole = Math.floor(rounded);
  const fils = Math.round((rounded - whole) * 100);
  let out = `${intToWords(whole)} DIRHAMS`;
  if (fils > 0) out += ` AND ${intToWords(fils)} FILS`;
  return out + " ONLY";
}

export function fmtAED(n) {
  return (Number(n) || 0).toLocaleString("en-AE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function recalcRow(row) {
  const qty = parseFloat(row.qty) || 0;
  const price = parseFloat(row.unit_price) || 0;
  const vatPct = parseFloat(row.vat_percent) || 0;
  const subtotal = qty * price;
  const vat = subtotal * (vatPct / 100);
  return { ...row, total_excl: subtotal, total_incl: subtotal + vat };
}

export function calcTotals(items, discount = 0) {
  let gross = 0, vat = 0;
  items.forEach((it) => {
    const r = recalcRow(it);
    gross += r.total_excl;
    vat += r.total_incl - r.total_excl;
  });
  const net = gross + vat - (parseFloat(discount) || 0);
  return { gross_total: gross, vat_total: vat, net_total: net };
}
