"""
AR/AP API — Module Kế toán công nợ (phải thu / phải trả).
- AR: hóa đơn gom N job, track đã thu (v_job_ar_status).
- AP: bảng kê chi phí vendor/employee, track đã trả (v_ap_unbilled_costs).
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import logging, io, smtplib
from email.message import EmailMessage
import httpx

from app.db.supabase_client import get_supabase
from app.core.config import settings

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


class StatusUpdate(BaseModel):
    payment_status: Optional[str] = None   # unpaid/partial/paid
    paid_amount: Optional[float] = None
    paid_date: Optional[date] = None
    note: Optional[str] = None
    due_date: Optional[date] = None


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


@router.patch("/api/ar/invoices/{invoice_id}")
def edit_invoice(invoice_id: int, payload: StatusUpdate):
    """Sửa tình trạng / ghi chú / hạn HĐ."""
    sb = get_supabase()
    data = {k: (str(v) if isinstance(v, date) else v)
            for k, v in payload.dict().items() if v is not None}
    if not data:
        raise HTTPException(400, "Không có gì để sửa")
    upd = sb.table("ar_invoices").update(data).eq("invoice_id", invoice_id).execute().data
    if not upd:
        raise HTTPException(404, "Không tìm thấy hóa đơn")
    return {"invoice": upd[0]}


@router.delete("/api/ar/invoices/{invoice_id}")
def delete_invoice(invoice_id: int):
    """Xóa HĐ (ar_invoice_jobs tự xóa theo CASCADE) → job quay lại 'chưa xuất HĐ'."""
    sb = get_supabase()
    sb.table("ar_invoices").delete().eq("invoice_id", invoice_id).execute()
    return {"deleted": invoice_id}


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


@router.patch("/api/ap/bills/{bill_id}")
def edit_bill(bill_id: int, payload: StatusUpdate):
    """Sửa tình trạng / ghi chú / hạn bảng kê."""
    sb = get_supabase()
    data = {k: (str(v) if isinstance(v, date) else v)
            for k, v in payload.dict().items() if v is not None}
    if not data:
        raise HTTPException(400, "Không có gì để sửa")
    upd = sb.table("ap_bills").update(data).eq("bill_id", bill_id).execute().data
    if not upd:
        raise HTTPException(404, "Không tìm thấy bảng kê")
    return {"bill": upd[0]}


@router.delete("/api/ap/bills/{bill_id}")
def delete_bill(bill_id: int):
    """Xóa bảng kê (ap_bill_items tự xóa theo CASCADE) → chi phí quay lại 'chờ thanh toán'."""
    sb = get_supabase()
    sb.table("ap_bills").delete().eq("bill_id", bill_id).execute()
    return {"deleted": bill_id}


@router.get("/api/ap/bills/{bill_id}/items")
def bill_items(bill_id: int):
    """Chi tiết các dòng chi phí trong 1 bảng kê (kèm thông tin đối chiếu)."""
    sb = get_supabase()
    items = sb.table("ap_bill_items").select("cost_id,amount").eq("bill_id", bill_id).execute().data
    return {"items": items}


# ============ XUẤT EXCEL theo cost_ids đã chọn ============
def _build_statement_xlsx(costs: list, title: str) -> bytes:
    import openpyxl
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "BangKe"
    thin = Side(style='thin'); bd = Border(thin, thin, thin, thin)
    is_cus = any(c.get("is_customs") for c in costs)
    ws.merge_cells('A1:J1'); ws['A1'] = title
    ws['A1'].font = Font(bold=True, size=14); ws['A1'].alignment = Alignment(horizontal='center')
    ws['A2'] = f"Ngày xuất: {date.today().strftime('%d/%m/%Y')}"
    if is_cus:
        hdr = ['STT', 'Job No', 'Ngày', 'Tên phí', 'Số tờ khai', 'Đơn giá', 'SL', 'Thành tiền']
    else:
        hdr = ['STT', 'Job No', 'Ngày', 'Tên phí', 'Biển số', 'Tuyến', 'INV/BL', 'Số HĐ', 'Đơn giá', 'SL', 'Thành tiền']
    ws.append([]); ws.append(hdr); hr = ws.max_row
    for c in range(1, len(hdr) + 1):
        cell = ws.cell(hr, c); cell.font = Font(bold=True); cell.border = bd
        cell.fill = PatternFill('solid', fgColor='DDEBF7'); cell.alignment = Alignment(horizontal='center')
    total = 0
    for i, c in enumerate(costs, 1):
        amt = int(c.get("amount") or 0); total += amt
        nm = c.get("cost_name", "") + (" (chi hộ)" if c.get("is_reimbursement") else "")
        dt = str(c.get("cost_date") or "")
        if is_cus:
            row = [i, c.get("job_no"), dt, nm, c.get("declaration_no") or "", int(c.get("buying_rate") or 0), float(c.get("quantity") or 1), amt]
        else:
            row = [i, c.get("job_no"), dt, nm, c.get("plate_number") or "", c.get("route") or "",
                   c.get("bl_awb_no") or "", c.get("job_invoice_no") or "", int(c.get("buying_rate") or 0), float(c.get("quantity") or 1), amt]
        ws.append(row)
        for cc in range(1, len(hdr) + 1): ws.cell(ws.max_row, cc).border = bd
    trow = [''] * (len(hdr) - 5) + ['TỔNG CỘNG', '', '', total]
    ws.append(trow); tr = ws.max_row
    for c in range(1, len(hdr) + 1):
        ws.cell(tr, c).font = Font(bold=True); ws.cell(tr, c).border = bd
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return buf.getvalue()


class ExportRequest(BaseModel):
    cost_ids: List[int]
    title: Optional[str] = "BẢNG KÊ CHI PHÍ PHẢI TRẢ"


@router.post("/api/ap/export")
def export_selected(payload: ExportRequest):
    """Xuất Excel bảng kê cho các dòng chi phí đã tick chọn."""
    sb = get_supabase()
    costs = sb.table("v_ap_unbilled_costs").select("*").in_("cost_id", payload.cost_ids).execute().data
    if not costs:
        raise HTTPException(400, "Không có chi phí")
    xlsx = _build_statement_xlsx(costs, payload.title)
    return StreamingResponse(io.BytesIO(xlsx),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="bangke_{date.today()}.xlsx"'})


# ============ NOTIFY KẾ TOÁN ============
class NotifyConfig(BaseModel):
    telegram_id: Optional[str] = None
    email: Optional[str] = None


@router.get("/api/ap/notify-config")
def get_notify_config():
    sb = get_supabase()
    rows = sb.table("ap_notify_config").select("*").eq("is_active", True).execute().data
    return {"config": rows[0] if rows else None}


@router.post("/api/ap/notify-config")
def set_notify_config(payload: NotifyConfig):
    sb = get_supabase()
    sb.table("ap_notify_config").update({"is_active": False}).eq("is_active", True).execute()
    row = sb.table("ap_notify_config").insert({
        "role": "accountant", "telegram_id": payload.telegram_id, "email": payload.email,
    }).execute().data[0]
    return {"config": row}


class NotifyRequest(BaseModel):
    cost_ids: List[int]
    note: Optional[str] = None


@router.post("/api/ap/notify")
def notify_accountant(payload: NotifyRequest):
    """Gửi bảng kê chi phí sẽ thanh toán cho kế toán (Telegram + Email)."""
    sb = get_supabase()
    cfg = sb.table("ap_notify_config").select("*").eq("is_active", True).execute().data
    if not cfg:
        raise HTTPException(400, "Chưa cấu hình kế toán (telegram_id/email)")
    cfg = cfg[0]
    costs = sb.table("v_ap_unbilled_costs").select("*").in_("cost_id", payload.cost_ids).execute().data
    if not costs:
        raise HTTPException(400, "Không có chi phí")
    total = sum(int(c.get("amount") or 0) for c in costs)
    vendors = sorted(set(c.get("vendor_name") or "?" for c in costs))
    title = f"ĐỀ NGHỊ CHI — {', '.join(vendors)}"
    xlsx = _build_statement_xlsx(costs, title)
    fname = f"DeNghiChi_{date.today()}.xlsx"
    summary = (f"💸 <b>Đề nghị thanh toán</b>\n"
               f"NCC: {', '.join(vendors)}\n"
               f"Số khoản: {len(costs)}\n"
               f"Tổng: <b>{total:,.0f}đ</b>".replace(",", "."))
    if payload.note:
        summary += f"\nGhi chú: {payload.note}"
    sent = {"telegram": False, "email": False}

    # Telegram
    settings.resolve_telegram_token()
    tok = settings.TELEGRAM_BOT_TOKEN
    if cfg.get("telegram_id") and tok:
        try:
            with httpx.Client(timeout=30) as cli:
                cli.post(f"https://api.telegram.org/bot{tok}/sendDocument",
                    data={"chat_id": cfg["telegram_id"], "caption": summary, "parse_mode": "HTML"},
                    files={"document": (fname, xlsx,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
            sent["telegram"] = True
        except Exception as e:
            logger.error(f"Telegram notify fail: {e}")

    # Email
    smtp_host = getattr(settings, "SMTP_HOST", None)
    if cfg.get("email") and smtp_host:
        try:
            msg = EmailMessage()
            msg["Subject"] = title
            msg["From"] = getattr(settings, "SMTP_FROM", settings.SMTP_USER)
            msg["To"] = cfg["email"]
            msg.set_content(summary.replace("<b>", "").replace("</b>", ""))
            msg.add_attachment(xlsx, maintype="application",
                subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=fname)
            with smtplib.SMTP(smtp_host, int(getattr(settings, "SMTP_PORT", 587))) as s:
                s.starttls()
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                s.send_message(msg)
            sent["email"] = True
        except Exception as e:
            logger.error(f"Email notify fail: {e}")

    return {"sent": sent, "total": total, "count": len(costs)}
