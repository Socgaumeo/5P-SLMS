"""
AR/AP API — Module Kế toán công nợ (phải thu / phải trả).
- AR: hóa đơn gom N job, track đã thu (v_job_ar_status).
- AP: bảng kê chi phí vendor/employee, track đã trả (v_ap_unbilled_costs).
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import logging

from app.db.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============ MODELS ============
class InvoiceCreate(BaseModel):
    customer_id: int
    job_ids: List[int]
    invoice_no: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    vat_rate: Optional[float] = 10
    note: Optional[str] = None
    created_by: Optional[int] = None


class PaymentUpdate(BaseModel):
    paid_amount: float
    paid_date: Optional[date] = None


class BillCreate(BaseModel):
    vendor_id: Optional[int] = None
    employee_id: Optional[int] = None
    cost_ids: List[int]
    bill_no: Optional[str] = None
    due_date: Optional[date] = None
    note: Optional[str] = None
    created_by: Optional[int] = None


# ============ AR — PHẢI THU ============
@router.get("/api/ar/invoices")
def list_invoices(status: Optional[str] = None):
    sb = get_supabase()
    q = sb.table("ar_invoices").select("*").order("created_at", desc=True)
    if status:
        q = q.eq("payment_status", status)
    return {"invoices": q.execute().data}


@router.get("/api/ar/job-status")
def job_ar_status(state: Optional[str] = None):
    """Job nào đã xuất HĐ / đã thu / chưa xuất."""
    sb = get_supabase()
    q = sb.table("v_job_ar_status").select("*")
    if state:
        q = q.eq("ar_state", state)
    return {"jobs": q.execute().data}


@router.post("/api/ar/invoices")
def create_invoice(payload: InvoiceCreate):
    sb = get_supabase()
    # Tính tổng từ total_revenue các job
    jobs = sb.table("jobs").select("job_id,total_revenue,customer_id").in_(
        "job_id", payload.job_ids).execute().data
    if not jobs:
        raise HTTPException(400, "Không tìm thấy job")
    bad = [j["job_id"] for j in jobs if j["customer_id"] != payload.customer_id]
    if bad:
        raise HTTPException(400, f"Job {bad} không thuộc khách hàng này")
    subtotal = sum(float(j["total_revenue"] or 0) for j in jobs)
    vat = round(subtotal * (payload.vat_rate or 0) / 100)
    total = subtotal + vat
    inv = sb.table("ar_invoices").insert({
        "invoice_no": payload.invoice_no,
        "customer_id": payload.customer_id,
        "issue_date": str(payload.issue_date) if payload.issue_date else None,
        "due_date": str(payload.due_date) if payload.due_date else None,
        "subtotal": subtotal, "vat_amount": vat, "total": total,
        "note": payload.note, "created_by": payload.created_by,
    }).execute().data[0]
    for j in jobs:
        sb.table("ar_invoice_jobs").insert({
            "invoice_id": inv["invoice_id"], "job_id": j["job_id"],
            "allocated_amount": float(j["total_revenue"] or 0),
        }).execute()
    return {"invoice": inv, "job_count": len(jobs)}


@router.patch("/api/ar/invoices/{invoice_id}/payment")
def pay_invoice(invoice_id: int, payload: PaymentUpdate):
    sb = get_supabase()
    upd = sb.table("ar_invoices").update({
        "paid_amount": payload.paid_amount,
        "paid_date": str(payload.paid_date) if payload.paid_date else str(date.today()),
    }).eq("invoice_id", invoice_id).execute().data
    if not upd:
        raise HTTPException(404, "Không tìm thấy hóa đơn")
    return {"invoice": upd[0]}


# ============ AP — PHẢI TRẢ ============
@router.get("/api/ap/unbilled")
def unbilled_costs(vendor_id: Optional[int] = None, employee_id: Optional[int] = None):
    """Chi phí chưa lên bảng kê. Không filter → gom theo vendor."""
    sb = get_supabase()
    if vendor_id:
        rows = sb.table("v_ap_unbilled_costs").select("*").eq(
            "vendor_id", vendor_id).execute().data
        return {"costs": rows, "total": sum(float(r["amount"] or 0) for r in rows)}
    # summary theo vendor
    rows = sb.table("v_ap_unbilled_costs").select("*").execute().data
    agg = {}
    for r in rows:
        vid = r.get("vendor_id")
        if vid is None:
            continue
        a = agg.setdefault(vid, {"vendor_id": vid, "vendor_name": r.get("vendor_name"), "count": 0, "total": 0})
        a["count"] += 1
        a["total"] += float(r["amount"] or 0)
    return {"vendors": sorted(agg.values(), key=lambda x: -x["total"])}


@router.get("/api/ap/bills")
def list_bills(status: Optional[str] = None):
    sb = get_supabase()
    q = sb.table("ap_bills").select("*").order("created_at", desc=True)
    if status:
        q = q.eq("payment_status", status)
    return {"bills": q.execute().data}


@router.post("/api/ap/bills")
def create_bill(payload: BillCreate):
    sb = get_supabase()
    if not payload.vendor_id and not payload.employee_id:
        raise HTTPException(400, "Cần vendor_id hoặc employee_id")
    costs = sb.table("job_costs").select("cost_id,buying_rate,quantity").in_(
        "cost_id", payload.cost_ids).execute().data
    if not costs:
        raise HTTPException(400, "Không tìm thấy chi phí")
    total = sum(float(c["buying_rate"] or 0) * float(c.get("quantity") or 1) for c in costs)
    bill = sb.table("ap_bills").insert({
        "bill_no": payload.bill_no,
        "vendor_id": payload.vendor_id, "employee_id": payload.employee_id,
        "total_amount": total,
        "due_date": str(payload.due_date) if payload.due_date else None,
        "note": payload.note, "created_by": payload.created_by,
    }).execute().data[0]
    for c in costs:
        amt = float(c["buying_rate"] or 0) * float(c.get("quantity") or 1)
        sb.table("ap_bill_items").insert({
            "bill_id": bill["bill_id"], "cost_id": c["cost_id"], "amount": amt,
        }).execute()
    return {"bill": bill, "item_count": len(costs)}


@router.patch("/api/ap/bills/{bill_id}/payment")
def pay_bill(bill_id: int, payload: PaymentUpdate):
    sb = get_supabase()
    upd = sb.table("ap_bills").update({
        "paid_amount": payload.paid_amount,
        "paid_date": str(payload.paid_date) if payload.paid_date else str(date.today()),
    }).eq("bill_id", bill_id).execute().data
    if not upd:
        raise HTTPException(404, "Không tìm thấy bảng kê")
    return {"bill": upd[0]}
