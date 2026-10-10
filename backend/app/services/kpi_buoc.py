"""KPI NHẬP JOB theo bước — file "Yêu cầu nhập Job và sử dụng hệ thống V1" (chị Hà chốt 08/10/2026).

Mỗi dịch vụ đi qua các bước (Nhận lô → Lấy hàng → Giao → Đã giao → Giá → Đối chiếu…). Mỗi bước có:
  - danh sách Ô phải nhập + Chứng từ bắt buộc  (tiêu chí v0.6, khoá `buoc`)
  - mốc T = lúc việc thật sự xảy ra (khách confirm, lấy hàng xong, giao xong, thông quan…)
  - hạn KPI (T+4h, T+12h, D+1, T+2/T+5 ngày làm việc, cuối tháng)
KPI bước = lúc bước được nhập ĐỦ (lần đầu)  so với  hạn tính từ T.

`quet()` chạy nền (mỗi 30–60 giây): job nào vừa có thay đổi thì kiểm lại, bước nào vừa đủ thì ghi
job_step_done (lần đầu, có người làm). Cách quét bắt được MỌI đường ghi: web, Sen, script.
"""
import json
import logging
import pathlib
import re
import datetime as dt
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)
VN = ZoneInfo("Asia/Ho_Chi_Minh")
TC = json.loads((pathlib.Path(__file__).resolve().parent.parent / "config" / "tieu_chi_nhap_job.json").read_text(encoding="utf-8"))

# Ô trong file V1 → cột thật / khoá cũ trong service_details ("sd:")
ALIAS = {
    "nguoi_book": ["nguoi_book", "sd:nguoi_book", "sd:nguoi_booking"],
    "china_truck_plate": ["intl_truck_plate", "sd:china_truck_plate"],
    "vehicle_type": ["vehicle_kind", "sd:vehicle_type", "truck_capacity"],
    "truck_capacity": ["truck_capacity", "sd:vehicle_type"],
    "agent": ["agent_name", "sd:agent"],
    "cont_type": ["cont_type", "sd:cont_type"],
    "loai_cuoc": ["freight_term"],
    "nguoi_lien_he_giao": ["delivery_contact"],
    "thoi_gian_hoan_thanh": ["service_done_at"],
    "so_tk_chinh": ["cd_main_count"],
    "so_tk_nhanh": ["cd_branch_count"],
    "ngay_thong_quan": ["cleared_at"],
}
JOB_COLS = {"etd", "eta", "vat_invoice_no"}
TUY_CHON = {"special_requirements"}          # "Ghi chú" — chỉ ghi khi có, không tính thiếu
NHAN = {
    "nguoi_book": "Người đặt dịch vụ", "vehicle_type": "Loại xe", "truck_capacity": "Trọng tải xe",
    "invoice_numbers": "Số invoice", "origin_address": "Điểm lấy", "dest_address": "Điểm giao",
    "scheduled_date": "Ngày lấy", "scheduled_time": "Giờ lấy", "delivery_date": "Ngày giao",
    "weight_kg": "Trọng lượng", "volume_cbm": "Khối", "package_quantity": "Số kiện", "rate_unit": "Đơn vị tính phí",
    "xe": "Biển số / tài xế", "gia_mua": "Giá mua", "gia_ban": "Giá bán", "vat_invoice_no": "Số HĐ VAT",
    "incoterm": "Term", "etd": "ETD", "eta": "ETA", "seller_name": "Shipper", "buyer_name": "Consignee",
    "booking_no": "Số booking", "atd": "ATD", "vessel_flight": "Tàu/chuyến bay", "vendor_id": "Vendor",
    "agent": "Agent", "container_no": "Số cont", "cont_type": "Loại cont", "cargo_type": "Tên hàng",
    "mbl_no": "MBL", "bl_awb_no": "HBL/HAWB", "loai_cuoc": "Collect/Prepaid", "chargeable_weight_kg": "KL tính cước",
    "nguoi_lien_he_giao": "Người liên hệ giao", "cd_no": "Số tờ khai", "phan_luong": "Phân luồng",
    "declaration_datetime": "Ngày TK", "so_tk_chinh": "SL TK chính", "so_tk_nhanh": "SL TK nhánh",
    "ngay_thong_quan": "Ngày thông quan", "china_truck_plate": "Biển số xe QT", "route": "Tuyến",
    "customs_port": "Cửa khẩu", "package_unit": "Đơn vị", "thoi_gian_hoan_thanh": "Giờ xong dịch vụ",
}
DOC_NHAN = {"BBGH": "BBGH", "CD": "Tờ khai", "INVOICE": "Invoice", "DEBIT": "Debit/bảng kê", "AWB": "AWB",
            "BL": "B/L", "BOOKING": "File booking", "WEIGHT_SLIP": "Phiếu cân", "SERVICE_CONFIRM": "BB xác nhận DV"}


def _rong(v):
    return v is None or (isinstance(v, str) and not v.strip()) or v == [] or v == {}


def _sd(svc):
    sd = svc.get("service_details") or {}
    if isinstance(sd, str):
        try:
            sd = json.loads(sd)
        except Exception:
            sd = {}
    return sd


def doc_bat_buoc(s, svc_type):
    """Chứng từ ghi trong file → doc_type bắt buộc (None = không bắt buộc)."""
    l = s.lower().strip()
    if "nếu có" in l or "thu chi hộ" in l:
        return None
    if "bbgh" in l:
        if "hàng nhập và nội địa" in l and not re.search(r"(_IMP|_DOM)$|^TRUCKING|^BORDER_IMP", svc_type):
            return None
        return "BBGH"
    for pre, t in (("awb", "AWB"), ("bl ", "BL"), ("bl(", "BL"), ("cd", "CD"), ("invoice", "INVOICE"),
                   ("debit", "DEBIT"), ("booking", "BOOKING"), ("file đặt xe", "BOOKING"), ("phiếu cân", "WEIGHT_SLIP"),
                   ("biên bản xác nhận", "SERVICE_CONFIRM")):
        if l.startswith(pre):
            return t
    return None


def _co(col, job, svc, costs):
    if col in TUY_CHON:
        return True
    if col == "gia_mua":
        return any((c.get("buying_amount") or 0) > 0 for c in costs if c.get("svc_id") == svc["svc_id"])
    if col == "gia_ban":
        return any((c.get("selling_amount") or 0) > 0 for c in costs if c.get("svc_id") == svc["svc_id"])
    if col == "xe":
        return bool(_sd(svc).get("vehicle_plate") or svc.get("driver_id"))
    if col in JOB_COLS:
        return not _rong(job.get(col))
    sd = _sd(svc)
    for k in ALIAS.get(col, [col]):
        v = sd.get(k[3:]) if k.startswith("sd:") else svc.get(k)
        if not _rong(v):
            return True
    return False


def _ts(v):
    """Chuỗi ngày/giờ → datetime có múi giờ VN. Chỉ có ngày → coi là 23:59 ngày đó (cho nhân viên hết ngày)."""
    if _rong(v):
        return None
    s = str(v).replace(" ", "T")
    try:
        if len(s) == 10:
            return dt.datetime.fromisoformat(s).replace(hour=23, minute=59, tzinfo=VN)
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        # cột created_at không có múi giờ = giờ của máy chủ ghi (production Railway: UTC; máy test: giờ VN)
        return d if d.tzinfo else d.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)
    except ValueError:
        return None


def moc(buoc, svc, job, svcs):
    """Mốc T của bước: (datetime, tên mốc)."""
    ten = buoc["ten"].lower()

    def lay(field):
        if svc.get(field):
            return _ts(svc[field]), field
        vals = [_ts(s.get(field)) for s in svcs if s.get(field)]
        vals = [v for v in vals if v]
        return (max(vals), field + " (dịch vụ khác)") if vals else (None, field)

    st = svc["service_type_code"]
    if buoc["buoc"] == 1:
        if job.get("confirmed_at"):
            return _ts(job["confirmed_at"]), "giờ khách confirm"
        return _ts(job.get("created_at")), "lúc tạo job (chưa nhập giờ confirm)"
    if ten.startswith("thông quan"):
        return lay("cleared_at")
    if ten.startswith("thực hiện"):
        return lay("service_done_at")
    if ten.startswith("booking"):
        return lay("atd")
    if ten.startswith("lấy"):
        return lay("pickup_at")
    if "giá" in ten:
        if st.startswith("CUS"):
            return lay("cleared_at")
        if st.startswith(("WHS", "SVC", "LIFT")):
            return lay("service_done_at")
        return lay("delivered_at")
    return lay("delivered_at")   # giao hàng, hàng đến, đã giao, đối chiếu


def han(kpi, T):
    if not T:
        return None
    k = (kpi or "").lower()
    T = T.astimezone(VN)
    m = re.search(r"t\+\s*(\d+)\s*h", k)
    if m:
        return T + dt.timedelta(hours=int(m.group(1)))
    m = re.search(r"t\+\s*(\d+)\s*ngày", k)
    if m:                                     # ngày làm việc: bỏ Chủ nhật
        d, n = T, int(m.group(1))
        while n:
            d += dt.timedelta(days=1)
            if d.weekday() != 6:
                n -= 1
        return d
    m = re.search(r"d\+\s*(\d+)", k)
    if m:
        return (T + dt.timedelta(days=int(m.group(1)))).replace(hour=23, minute=59, second=59)
    if "30/31" in k:
        nxt = (T.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        return (nxt - dt.timedelta(days=1)).replace(hour=23, minute=59, second=59)
    return None


def danh_gia_job(client, job_id):
    """Kiểm từng dịch vụ × bước: thiếu ô nào, thiếu chứng từ nào, mốc T, hạn."""
    job = (client.table("jobs").select("*").eq("job_id", job_id).limit(1).execute().data or [None])[0]
    if not job:
        return []
    svcs = [s for s in (client.table("job_services").select("*").eq("job_id", job_id).execute().data or [])
            if (s.get("status_code") or "") != "CANCELLED"]
    docs = {d["doc_type"] for d in (client.table("documents").select("doc_type").eq("job_id", job_id).execute().data or [])}
    costs = client.table("job_costs").select("svc_id,buying_amount,selling_amount").eq("job_id", job_id).execute().data or []
    out = []
    for svc in svcs:
        tc = TC["dich_vu"].get(svc["service_type_code"]) or {}
        for b in tc.get("buoc", []):
            thieu_o = [c for c in b.get("cot", []) if not _co(c, job, svc, costs)]
            can_doc = [t for t in (doc_bat_buoc(x, svc["service_type_code"]) for x in b.get("chung_tu", [])) if t]
            thieu_ct = [t for t in dict.fromkeys(can_doc) if t not in docs]
            T, ten_moc = moc(b, svc, job, svcs)
            out.append({"job_id": job_id, "job_no": job["job_no"], "created_by": job.get("created_by"),
                        "svc_id": svc["svc_id"], "svc_type": svc["service_type_code"],
                        "buoc": b["buoc"], "ten_buoc": b["ten"], "trang_thai": b.get("trang_thai"), "kpi": b.get("kpi"),
                        "thieu_o": thieu_o, "thieu_ct": thieu_ct, "du": not thieu_o and not thieu_ct,
                        "T": T, "ten_moc": ten_moc, "han": han(b.get("kpi"), T)})
    return out


def _actor(client, job_id):
    ev = client.table("job_events").select("actor").eq("job_id", job_id).neq("actor", "unknown") \
        .order("event_id", desc=True).limit(1).execute().data
    return ev[0]["actor"] if ev else "unknown"


def ghi_buoc_du(client, job_id):
    """Ghi LẦN ĐẦU các bước vừa đủ. Không ghi đè (unique svc_id+buoc)."""
    rows = [r for r in danh_gia_job(client, job_id) if r["du"]]
    if not rows:
        return 0
    da = {(x["svc_id"], x["buoc"]) for x in (client.table("job_step_done").select("svc_id,buoc")
                                             .eq("job_id", job_id).execute().data or [])}
    moi = [r for r in rows if (r["svc_id"], r["buoc"]) not in da]
    if not moi:
        return 0
    actor = _actor(client, job_id)
    client.table("job_step_done").upsert([{
        "job_id": r["job_id"], "svc_id": r["svc_id"], "svc_type": r["svc_type"], "buoc": r["buoc"],
        "ten_buoc": r["ten_buoc"], "trang_thai": r["trang_thai"], "kpi": r["kpi"], "actor": actor,
    } for r in moi], on_conflict="svc_id,buoc", ignore_duplicates=True).execute()
    return len(moi)


def quet(client, phut=1440):
    """Quét job có thay đổi gần đây (lịch sử sự kiện + dịch vụ sửa)."""
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=phut)).isoformat()
    ids = {e["job_id"] for e in (client.table("job_events").select("job_id").gte("event_at", since).execute().data or [])}
    since_local = (dt.datetime.now() - dt.timedelta(minutes=phut)).isoformat()
    ids |= {s["job_id"] for s in (client.table("job_services").select("job_id").gte("updated_at", since_local).execute().data or [])}
    n = 0
    for jid in sorted(ids):
        try:
            n += ghi_buoc_du(client, jid)
        except Exception as e:
            logger.warning(f"[kpi] job {jid}: {e}")
    return n


def bat_dau_quet_nen(get_client, giay=30):
    import threading
    import time

    def chay():
        while True:
            try:
                n = quet(get_client())
                if n:
                    logger.info(f"[kpi] ghi {n} bước vừa đủ")
            except Exception as e:
                logger.warning(f"[kpi] quét lỗi: {e}")
            time.sleep(giay)
    threading.Thread(target=chay, daemon=True).start()
