"""Ansary Furniture - Tax Invoice & Customer Management API."""
from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import uuid
import logging
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from num2words import num2words

from pdf_generator import build_invoice_pdf

# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def amount_to_words(amount: float) -> str:
    """Convert AED amount to words: e.g. 1520.50 -> 'ONE THOUSAND FIVE HUNDRED TWENTY DIRHAMS AND FIFTY FILS ONLY'."""
    try:
        amount = round(float(amount), 2)
        whole = int(amount)
        fils = int(round((amount - whole) * 100))
        words = num2words(whole).upper().replace("-", " ").replace(",", "")
        out = f"{words} DIRHAMS"
        if fils > 0:
            fils_words = num2words(fils).upper().replace("-", " ").replace(",", "")
            out += f" AND {fils_words} FILS"
        return out + " ONLY"
    except Exception:
        return "ZERO DIRHAMS ONLY"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str


class CustomerIn(BaseModel):
    customer_trn: str = ""
    company_name: str = ""
    contact_person: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""


class Customer(CustomerIn):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=now_utc)
    updated_at: str = Field(default_factory=now_utc)


class InvoiceItemIn(BaseModel):
    description: str = ""
    qty: float = 0
    unit: str = ""
    unit_price: float = 0
    vat_percent: float = 5
    total_excl: float = 0
    total_incl: float = 0


class InvoiceIn(BaseModel):
    invoice_no: Optional[str] = None
    date: str  # ISO date
    do_no: str = ""
    lpo_no: str = ""
    customer: CustomerIn
    items: List[InvoiceItemIn] = []
    gross_total: float = 0
    discount: float = 0
    vat_total: float = 0
    net_total: float = 0
    amount_words: str = ""
    notes: str = ""
    terms: str = ""


class SettingsModel(BaseModel):
    company_name: str = "ANSARY FURNITURE"
    tagline: str = "LET'S DECORATE YOUR HOME"
    trn: str = "104305978900003"
    address: str = "Hassan Bin Haitham Street - Industrial Area-2, Ajman, UAE"
    email: str = "info@ansaryfurniture.com"
    phone: str = "0568680827"
    website: str = "www.ansaryfurniture.com"
    extra_websites: List[str] = [
        "www.repairsofadubai.ae - 0566057658",
        "www.dubai-curtain.ae - 0527843396",
    ]
    bank_name: str = "Abu Dhabi Commercial Bank PJSC"
    account_title: str = "ANSARY FURNITURE"
    account_number: str = "12330553820001"
    iban: str = "AE020300123305538200001"
    currency: str = "AED"
    branch: str = "IBD - Al Jurf Branch"
    swift_code: str = "ADCBAEAA"
    default_vat: float = 5
    invoice_prefix: str = "AF-"
    logo_url: str = ""
    signature_url: str = ""
    stamp_url: str = ""


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Ansary Furniture API")
api = APIRouter(prefix="/api")


# ---------- Auth ----------
@api.post("/auth/login")
async def login(payload: LoginRequest, response: Response):
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"], user["email"])
    response.set_cookie(
        key="access_token", value=token, httponly=True, secure=False,
        samesite="lax", max_age=8 * 3600, path="/",
    )
    return {"id": user["id"], "email": user["email"], "name": user.get("name", "Admin"), "token": token}


@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user


UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_KINDS = {"logo", "signature", "stamp"}


@api.post("/settings/upload/{kind}")
async def upload_asset(kind: str, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if kind not in ALLOWED_KINDS:
        raise HTTPException(status_code=400, detail="Invalid asset kind")
    ext = (file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "png").lower()
    if ext not in {"png", "jpg", "jpeg", "webp"}:
        raise HTTPException(status_code=400, detail="Only PNG/JPG/WEBP allowed")
    fname = f"{kind}.{ext}"
    dest = UPLOAD_DIR / fname
    # remove any prior file with a different extension
    for old in UPLOAD_DIR.glob(f"{kind}.*"):
        if old.name != fname:
            try: old.unlink()
            except Exception: pass
    contents = await file.read()
    dest.write_bytes(contents)
    url = f"/api/uploads/{fname}"
    field = f"{kind}_url"
    await db.settings.update_one({"_id": "default"}, {"$set": {field: url}}, upsert=True)
    return {"url": url}


@api.delete("/settings/upload/{kind}")
async def delete_asset(kind: str, user: dict = Depends(get_current_user)):
    if kind not in ALLOWED_KINDS:
        raise HTTPException(status_code=400, detail="Invalid asset kind")
    for old in UPLOAD_DIR.glob(f"{kind}.*"):
        try: old.unlink()
        except Exception: pass
    field = f"{kind}_url"
    await db.settings.update_one({"_id": "default"}, {"$set": {field: ""}}, upsert=True)
    return {"ok": True}


# ---------- Settings ----------
@api.get("/settings/public")
async def public_settings():
    """Public branding info — used by login page logo display."""
    doc = await db.settings.find_one({"_id": "default"}, {"_id": 0}) or SettingsModel().model_dump()
    return {
        "company_name": doc.get("company_name", ""),
        "tagline": doc.get("tagline", ""),
        "logo_url": doc.get("logo_url", ""),
    }


@api.get("/settings")
async def get_settings(user: dict = Depends(get_current_user)):
    doc = await db.settings.find_one({"_id": "default"}, {"_id": 0})
    if not doc:
        defaults = SettingsModel().model_dump()
        await db.settings.insert_one({"_id": "default", **defaults})
        return defaults
    return doc


@api.put("/settings")
async def update_settings(payload: SettingsModel, user: dict = Depends(get_current_user)):
    doc = payload.model_dump()
    await db.settings.update_one({"_id": "default"}, {"$set": doc}, upsert=True)
    return doc


# ---------- Customers ----------
@api.get("/customers")
async def list_customers(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    query: dict = {}
    if q:
        rx = {"$regex": q, "$options": "i"}
        query = {"$or": [
            {"customer_trn": rx}, {"company_name": rx}, {"contact_person": rx},
            {"phone": rx}, {"email": rx}, {"address": rx},
        ]}
    total = await db.customers.count_documents(query)
    cur = db.customers.find(query, {"_id": 0}).sort("updated_at", -1).skip(skip).limit(limit)
    items = await cur.to_list(length=limit)
    return {"items": items, "total": total}


@api.get("/customers/search")
async def search_customers(q: str = Query("", min_length=0), user: dict = Depends(get_current_user)):
    """Lightweight autocomplete by TRN prefix or company name."""
    if not q:
        return []
    rx = {"$regex": f"^{q}", "$options": "i"}
    cur = db.customers.find(
        {"$or": [{"customer_trn": rx}, {"company_name": rx}]},
        {"_id": 0},
    ).limit(8)
    return await cur.to_list(length=8)


@api.get("/customers/by-trn/{trn}")
async def get_customer_by_trn(trn: str, user: dict = Depends(get_current_user)):
    doc = await db.customers.find_one({"customer_trn": trn}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Customer not found")
    return doc


@api.post("/customers")
async def create_customer(payload: CustomerIn, user: dict = Depends(get_current_user)):
    doc = Customer(**payload.model_dump()).model_dump()
    if doc["customer_trn"]:
        existing = await db.customers.find_one({"customer_trn": doc["customer_trn"]}, {"_id": 0})
        if existing:
            return {"existing": True, "customer": existing}
    await db.customers.insert_one(doc)
    doc.pop("_id", None)
    return {"existing": False, "customer": doc}


@api.put("/customers/{cid}")
async def update_customer(cid: str, payload: CustomerIn, user: dict = Depends(get_current_user)):
    upd = payload.model_dump()
    upd["updated_at"] = now_utc()
    r = await db.customers.update_one({"id": cid}, {"$set": upd})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    doc = await db.customers.find_one({"id": cid}, {"_id": 0})
    return doc


@api.delete("/customers/{cid}")
async def delete_customer(cid: str, user: dict = Depends(get_current_user)):
    await db.customers.delete_one({"id": cid})
    return {"ok": True}


# ---------- Invoices ----------
async def _next_invoice_no() -> str:
    settings = await db.settings.find_one({"_id": "default"})
    prefix = (settings or {}).get("invoice_prefix", "AF-")
    seq = await db.counters.find_one_and_update(
        {"_id": "invoice"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=True,
    )
    n = (seq or {"value": 1}).get("value", 1)
    return f"{prefix}{n:06d}"


@api.get("/invoices/next-number")
async def next_invoice_number(user: dict = Depends(get_current_user)):
    # peek without incrementing
    settings = await db.settings.find_one({"_id": "default"})
    prefix = (settings or {}).get("invoice_prefix", "AF-")
    seq = await db.counters.find_one({"_id": "invoice"})
    n = (seq or {"value": 0}).get("value", 0) + 1
    return {"invoice_no": f"{prefix}{n:06d}"}


async def _upsert_customer_from_invoice(c: dict) -> str:
    """Save/update customer; return customer_id."""
    if not (c.get("customer_trn") or c.get("company_name")):
        return ""
    query = {"customer_trn": c["customer_trn"]} if c.get("customer_trn") else {"company_name": c["company_name"]}
    existing = await db.customers.find_one(query)
    if existing:
        upd = {k: c.get(k, "") for k in ["company_name", "contact_person", "phone", "email", "address", "customer_trn"]}
        upd["updated_at"] = now_utc()
        await db.customers.update_one({"id": existing["id"]}, {"$set": upd})
        return existing["id"]
    new = Customer(**c).model_dump()
    await db.customers.insert_one(new)
    new.pop("_id", None)
    return new["id"]


@api.post("/invoices")
async def create_invoice(payload: InvoiceIn, user: dict = Depends(get_current_user)):
    data = payload.model_dump()
    if not data.get("invoice_no"):
        data["invoice_no"] = await _next_invoice_no()
    else:
        # ensure counter stays ahead if admin overrides
        try:
            num = int("".join(ch for ch in data["invoice_no"] if ch.isdigit()) or 0)
            await db.counters.update_one({"_id": "invoice"}, {"$max": {"value": num}}, upsert=True)
        except Exception:
            pass

    data["id"] = str(uuid.uuid4())
    data["created_at"] = now_utc()
    data["updated_at"] = now_utc()
    data["customer_id"] = await _upsert_customer_from_invoice(data["customer"])

    # Compute amount in words if not provided
    if not data.get("amount_words"):
        data["amount_words"] = amount_to_words(data.get("net_total", 0))

    await db.invoices.insert_one(data)
    data.pop("_id", None)
    return data


@api.get("/invoices")
async def list_invoices(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    query: dict = {}
    if q:
        rx = {"$regex": q, "$options": "i"}
        query = {"$or": [
            {"invoice_no": rx},
            {"customer.customer_trn": rx},
            {"customer.company_name": rx},
            {"customer.contact_person": rx},
            {"customer.phone": rx},
            {"customer.email": rx},
        ]}
    total = await db.invoices.count_documents(query)
    cur = db.invoices.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    items = await cur.to_list(length=limit)
    return {"items": items, "total": total}


@api.get("/invoices/{iid}")
async def get_invoice(iid: str, user: dict = Depends(get_current_user)):
    doc = await db.invoices.find_one({"id": iid}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return doc


@api.put("/invoices/{iid}")
async def update_invoice(iid: str, payload: InvoiceIn, user: dict = Depends(get_current_user)):
    data = payload.model_dump()
    data["updated_at"] = now_utc()
    data["customer_id"] = await _upsert_customer_from_invoice(data["customer"])
    if not data.get("amount_words"):
        data["amount_words"] = amount_to_words(data.get("net_total", 0))
    r = await db.invoices.update_one({"id": iid}, {"$set": data})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    doc = await db.invoices.find_one({"id": iid}, {"_id": 0})
    return doc


@api.delete("/invoices/{iid}")
async def delete_invoice(iid: str, user: dict = Depends(get_current_user)):
    await db.invoices.delete_one({"id": iid})
    return {"ok": True}


@api.get("/invoices/{iid}/pdf")
async def invoice_pdf(iid: str, request: Request):
    # allow query token fallback for direct browser open
    token = request.query_params.get("token")
    if token:
        try:
            jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
    else:
        await get_current_user(request)
    doc = await db.invoices.find_one({"id": iid}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Invoice not found")
    settings = await db.settings.find_one({"_id": "default"}, {"_id": 0}) or SettingsModel().model_dump()
    pdf_bytes = build_invoice_pdf(doc, settings)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{doc["invoice_no"]}.pdf"'},
    )


@api.post("/invoices/preview-pdf")
async def preview_pdf(payload: InvoiceIn, user: dict = Depends(get_current_user)):
    """Generate PDF without saving — used for 'Print / Save PDF' before clicking save."""
    data = payload.model_dump()
    if not data.get("invoice_no"):
        data["invoice_no"] = "DRAFT"
    if not data.get("amount_words"):
        data["amount_words"] = amount_to_words(data.get("net_total", 0))
    settings = await db.settings.find_one({"_id": "default"}, {"_id": 0}) or SettingsModel().model_dump()
    pdf_bytes = build_invoice_pdf(data, settings)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{data["invoice_no"]}.pdf"'},
    )


# ---------- Dashboard ----------
@api.get("/dashboard/stats")
async def dashboard_stats(user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date().isoformat()
    month = datetime.now(timezone.utc).strftime("%Y-%m")

    pipeline_today = [
        {"$match": {"date": today}},
        {"$group": {"_id": None, "count": {"$sum": 1}, "revenue": {"$sum": "$net_total"}, "vat": {"$sum": "$vat_total"}}},
    ]
    pipeline_month = [
        {"$match": {"date": {"$regex": f"^{month}"}}},
        {"$group": {"_id": None, "count": {"$sum": 1}, "revenue": {"$sum": "$net_total"}, "vat": {"$sum": "$vat_total"}}},
    ]

    today_agg = await db.invoices.aggregate(pipeline_today).to_list(1)
    month_agg = await db.invoices.aggregate(pipeline_month).to_list(1)

    total_invoices = await db.invoices.count_documents({})
    total_customers = await db.customers.count_documents({})

    # Last 6 months trend
    months_trend = []
    for i in range(5, -1, -1):
        d = datetime.now(timezone.utc).replace(day=1) - timedelta(days=30 * i)
        m = d.strftime("%Y-%m")
        agg = await db.invoices.aggregate([
            {"$match": {"date": {"$regex": f"^{m}"}}},
            {"$group": {"_id": None, "revenue": {"$sum": "$net_total"}, "count": {"$sum": 1}}},
        ]).to_list(1)
        months_trend.append({
            "month": d.strftime("%b"),
            "revenue": (agg[0]["revenue"] if agg else 0),
            "count": (agg[0]["count"] if agg else 0),
        })

    # Top customers
    top = await db.invoices.aggregate([
        {"$group": {"_id": "$customer.company_name", "total": {"$sum": "$net_total"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 5},
    ]).to_list(5)

    return {
        "today_invoices": (today_agg[0]["count"] if today_agg else 0),
        "today_revenue": (today_agg[0]["revenue"] if today_agg else 0),
        "monthly_revenue": (month_agg[0]["revenue"] if month_agg else 0),
        "monthly_invoices": (month_agg[0]["count"] if month_agg else 0),
        "vat_collected": (month_agg[0]["vat"] if month_agg else 0),
        "total_invoices": total_invoices,
        "total_customers": total_customers,
        "trend": months_trend,
        "top_customers": [{"name": t["_id"] or "Unknown", "total": t["total"], "count": t["count"]} for t in top],
    }


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
app.mount("/api/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.customers.create_index("customer_trn")
    await db.customers.create_index("company_name")
    await db.invoices.create_index("invoice_no", unique=True)
    await db.invoices.create_index("date")

    admin_email = os.environ.get("ADMIN_EMAIL", "admin@ansaryfurniture.com").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@123")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Admin",
            "role": "admin",
            "created_at": now_utc(),
        })
        logger.info(f"Seeded admin user: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}},
        )

    # Default settings
    await db.settings.update_one(
        {"_id": "default"},
        {"$setOnInsert": SettingsModel().model_dump()},
        upsert=True,
    )
    # Backfill any missing fields for older docs
    defaults = SettingsModel().model_dump()
    existing_settings = await db.settings.find_one({"_id": "default"}) or {}
    missing = {k: v for k, v in defaults.items() if k not in existing_settings}
    if missing:
        await db.settings.update_one({"_id": "default"}, {"$set": missing})
    # If we have a default logo bundled on disk, point settings to it
    default_logo = UPLOAD_DIR / "logo.png"
    if default_logo.exists():
        await db.settings.update_one(
            {"_id": "default"},
            {"$set": {"logo_url": "/api/uploads/logo.png"}},
            upsert=True,
        )


@app.on_event("shutdown")
async def shutdown():
    client.close()
