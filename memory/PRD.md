# Ansary Furniture — Tax Invoice & Customer Management System

## Original Problem Statement
Build a modern, professional, responsive Tax Invoice Web Application for Ansary Furniture with: invoice creation, automatic customer database with TRN-based real-time autofill & suggestions, dynamic line items with automatic VAT calculations, save invoices, print/export PDF that visually matches the provided invoice template, invoice history, customer management, dashboard with charts, settings page for company/bank details, JWT admin login, responsive UI (blue/white/orange ERP theme).

## Architecture (delivered)
- **Frontend:** React 19 + Tailwind + React Router + Recharts + Sonner toasts.
- **Backend:** FastAPI + Motor (MongoDB) + bcrypt/JWT + ReportLab + num2words.
- **Database:** MongoDB collections — `users`, `customers`, `invoices`, `settings`, `counters`.
- **PDF:** Server-side ReportLab generator at `/api/invoices/{id}/pdf` matching the supplied invoice template (logo, header, customer block, items table padded to 12 rows, totals box, bank details, signature area).

## User Personas
- **Admin / Staff** — single role; creates invoices, manages customers, configures company/bank settings.

## Core Requirements (static)
1. Real-time customer autofill by TRN (autocomplete + exact-match autofill).
2. Auto-incrementing invoice number with admin override (`AF-NNNNNN`).
3. Auto VAT 5% per row (editable), auto totals, auto amount-in-words.
4. PDF that visually matches the Ansary Furniture template.
5. JWT-protected admin login.
6. Customer DB auto-upsert on every invoice save.

## What's been implemented (2026-06-26)
- ✅ JWT login (`/api/auth/login`, `/me`, `/logout`) + admin seed + protected routes.
- ✅ Invoice editor with TRN autofill + autocomplete suggestions, dynamic rows, duplicate/delete, reactive totals, amount in words, discount, notes, terms, keyboard shortcuts (Ctrl+S/P/N).
- ✅ Save & update invoices with auto invoice numbering and customer upsert.
- ✅ Invoice history with search, edit, duplicate, delete, PDF download.
- ✅ Customer management page (CRUD + search).
- ✅ Settings page (company info, bank details, default VAT, invoice prefix).
- ✅ Dashboard with KPI cards + monthly revenue bar chart + invoice count line chart + top customers.
- ✅ Server-side PDF (`reportlab`) closely matching the provided template.
- ✅ Right sidebar Search Records (search by invoice no, TRN, company, email, phone).
- ✅ Responsive layout, orange/navy ERP theme, soft shadows, rounded cards.

## Test credentials
- Admin: `admin@ansaryfurniture.com` / `Admin@123`

## Prioritized Backlog
**P1 (next iterations)**
- FTA-compliant QR code (UAE TRN + invoice fields) embedded in PDF.
- Excel import/export for customers and invoices.
- Email / WhatsApp invoice delivery.
- Upload company logo, signature, stamp images via Settings.

**P2**
- Dark mode toggle.
- Multi-user roles (manager/staff/viewer) with permissions.
- Auto-save draft invoices (localStorage).
- Forgot-password flow with email.
- Recent / favorite customers shortcut chips.

## Known limitations
- PDF logo is a vector recreation (not the exact original Ansary image). Replace by enabling logo upload from Settings (P1).
- Tech stack is React + FastAPI + MongoDB (problem statement requested Node+MySQL — environment forces this choice for reliable preview/deploy).
