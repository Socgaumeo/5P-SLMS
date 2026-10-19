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
TUY_CHON = {"special_requirements", "scheduled_date"}   # 16/10 Khánh: Ngày lấy không tính KPI, chỉ ghi khi có          # "Ghi chú" — chỉ ghi khi có, không tính thiếu
NHAN = {"ky_thanh_toan": "Kỳ thanh toán", 
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
DOC_NHAN = {"INVOICE_VAT": "Hoá đơn VAT đầu ra", "BBGH": "BBGH", "CD": "Tờ khai", "INVOICE": "Invoice", "DEBIT": "Debit/bảng kê", "AWB": "AWB",
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


# 13/10 (Khánh): ô số đo bắt buộc theo ĐƠN VỊ TÍNH PHÍ người dùng chọn (rate_unit, chọn từ DB cho đúng thực tế).
# Tính theo chuyến / xe / container → không cần số khối. Đơn vị theo khối (CBM) → bắt buộc có khối.
DON_VI_KHONG_CAN_KHOI = {"TRIP", "CHUYEN", "CHUYẾN", "XE", "CONT", "CONTAINER", "CA", "SHIFT", "LO", "LÔ", "TK", "TO KHAI"}


def _mien_theo_don_vi(col, svc):
    u = str(svc.get("rate_unit") or "").strip().upper()
    # 15/10 (Khánh): tính tiền theo chuyến/xe/cont → trọng lượng chỉ để tham khảo, KHÔNG bắt buộc (như số khối).
    if col in ("volume_cbm", "weight_kg") and u in DON_VI_KHONG_CAN_KHOI:
        return True
    return False


def _co(col, job, svc, costs):
    if col in TUY_CHON:
        return True
    if _mien_theo_don_vi(col, svc):
        return True
    if col == "chargeable_weight_kg" and not svc["service_type_code"].startswith(("AIR", "SEA")):
        # 16/10 Khánh: vận chuyển đã có GIÁ MUA mà tính theo chuyến/cont/xe ⇒ KL tính cước không cần.
        u = str(svc.get("rate_unit") or "").strip().upper()
        co_gia_mua = any((c.get("buying_amount") or 0) > 0 for c in costs if c.get("svc_id") in (svc["svc_id"], None))
        if co_gia_mua and u in DON_VI_KHONG_CAN_KHOI:
            return True
    if col == "gia_mua" and _sd(svc).get("tu_lam") is True:
        return True   # Khánh 13/10: CHỈ khi người dùng XÁC NHẬN dịch vụ do 5P tự làm (service_details.tu_lam=true)
                      # → không có chi phí thuê ngoài. Không vendor KHÔNG tự suy là tự làm (có thể quên điền).
    if col == "gia_mua":
        # 13/10: dòng phí ghi cấp job (svc_id trống) tính cho mọi dịch vụ của job
        return any((c.get("buying_amount") or 0) > 0 for c in costs if c.get("svc_id") in (svc["svc_id"], None))
    if col == "gia_ban":
        # 13/10: dòng phí ghi cấp job (svc_id trống) tính cho mọi dịch vụ của job
        return any((c.get("selling_amount") or 0) > 0 for c in costs if c.get("svc_id") in (svc["svc_id"], None))
    if col == "xe":
        # 14/10 (Khánh): xe CBT là phương tiện trên tờ khai (biển xe QT, VD KA5798) — lưu ở
        # service_details.truck_plate / china_truck_plate hoặc cột intl_truck_plate, không chỉ vehicle_plate.
        sd = _sd(svc)
        return bool(sd.get("vehicle_plate") or sd.get("truck_plate") or sd.get("china_truck_plate")
                    or svc.get("intl_truck_plate") or svc.get("driver_id"))
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


# ── Mốc T = THAO TÁC của nhân viên / Sen (Khánh chốt 10/10): không nhập tay giờ ──
_DI = ("ASSIGNED", "DISPATCHED", "IN_TRANSIT", "IN_PROGRESS")
_XONG = ("DELIVERED", "COMPLETED")


def _ev_ts(e):
    return _ts(e["event_at"])


def _dau_tien(evs, ok, nhan):
    hit = sorted((e for e in evs if ok(e)), key=lambda e: e["event_at"])
    if not hit:
        return None, nhan
    e = hit[0]
    return _ev_ts(e), f"{nhan} ({e.get('actor') or 'unknown'})"


def moc(buoc, svc, job, svcs, evs):
    """Mốc T của bước = lần đầu có THAO TÁC báo việc đó đã xảy ra. Trả (datetime, mô tả nguồn)."""
    sid = svc["svc_id"]
    ten = buoc["ten"].lower()
    st = svc["service_type_code"]
    cua_dv = [e for e in evs if e.get("svc_id") in (sid, None)]

    def nhan_lo():
        # Khánh chốt 12/10: job có mail (mail đến TRƯỚC khi tạo job) → T = lúc mail có đủ thông tin tạo job;
        # không có mail / mail đến sau khi tạo job → T = lúc nhân viên tạo job.
        t_tao, n_tao = _dau_tien(evs, lambda e: True, "tạo job")
        # 16/10: job tạo trước khi có bảng sự kiện → sự kiện đầu tiên có thể là Sen tự cập nhật muộn
        # (VD điền lại từ tờ khai) ⇒ lấy giờ tạo job thật nếu sớm hơn.
        tj = _ts(job.get("created_at")) if not _rong(job.get("created_at")) else None
        if tj and (not t_tao or tj < t_tao):
            t_tao, n_tao = tj, "tạo job"
        m = job.get("_mail_dau")
        if m and t_tao and m["t"] < t_tao:
            return m["t"], f"mail {m['loai'].lower()} {m['t'].astimezone(VN):%d/%m %H:%M} ({m['nguoi']})"
        return t_tao, n_tao

    def lay_hang():
        return _dau_tien(cua_dv, lambda e: (e["event_type"] == "MOC" and e["field"] in ("vehicle_plate", "driver_id"))
                         or (e["event_type"] == "SVC_STATUS" and e["to_value"] in _DI and e.get("svc_id") == sid),
                         "gán xe / chuyển đang chạy")

    def giao():
        # Khánh chốt 14/10: delivery_date = ngày giao DỰ KIẾN (bắt buộc ở bước giao hàng) — KHÔNG phải mốc đã giao.
        # Mốc đã giao = GIỜ GIAO THỰC TẾ (job_services.delivered_at). Job cũ chưa nhập giờ thực tế → lấy lần
        # đầu tải BBGH / đổi trạng thái Đã giao (trạng thái này chỉ đổi khi đã có BBGH).
        if "delivered_at" in svc and not _rong(svc.get("delivered_at")):
            t = _ts(svc["delivered_at"])
            if t:
                return t, "giờ giao thực tế"
        return _dau_tien(cua_dv, lambda e: (e["event_type"] == "DOC" and e["to_value"] == "BBGH")
                         or (e["event_type"] == "SVC_STATUS" and e["to_value"] in _XONG and e.get("svc_id") == sid)
                         or (e["event_type"] == "STATUS" and e["to_value"] == "DELIVERED"),
                         "tải BBGH / báo đã giao")

    def thong_quan():
        # 16/10 Khánh: dịch vụ CUS tính từ GIỜ THÔNG QUAN in trên tờ khai (Sen tự đọc tờ khai), không từ lúc nhập/tải.
        if st.startswith("CUS") and not _rong(svc.get("cleared_at")):
            t = _ts(svc["cleared_at"])
            if t:
                return t, "giờ thông quan trên tờ khai"
        return _dau_tien(cua_dv, lambda e: (e["event_type"] == "MOC" and e["field"] in ("cd_no", "declaration_datetime") and e.get("svc_id") == sid)
                         or (e["event_type"] == "DOC" and e["to_value"] == "CD")
                         or (e["event_type"] == "SVC_STATUS" and e["to_value"] in ("CUS_APPROVED", "COMPLETED") and e.get("svc_id") == sid),
                         "nhập số tờ khai / tải tờ khai")

    def van_don():
        # 16/10 Khánh: không biết lúc nào AWB/BL có ⇒ tính từ lúc AWB/BL xuất hiện (mail gửi vận đơn,
        # hoặc lúc tải/nhập số vận đơn — lấy cái SỚM nhất) + KPI. Thường Sen tự đọc mail và điền.
        t, n = _dau_tien(cua_dv, lambda e: (e["event_type"] == "MOC" and e["field"] in ("bl_awb_no", "mbl_no", "atd") and e.get("svc_id") == sid)
                         or (e["event_type"] == "DOC" and e["to_value"] in ("AWB", "BL")),
                         "nhập vận đơn / tải AWB-BL")
        mb = next((m for m in job.get("_mails") or [] if m.get("event_type") == "BILL"), None)
        tm = _ts(mb["mail_date"]) if mb else None
        if tm and (not t or tm < t):
            return tm, f"mail vận đơn {tm.astimezone(VN):%d/%m %H:%M} ({(mb.get('sender') or '')[:30]})"
        return t, n

    def xong_dv():
        return _dau_tien(cua_dv, lambda e: (e["event_type"] == "SVC_STATUS" and e["to_value"] == "COMPLETED" and e.get("svc_id") == sid)
                         or (e["event_type"] == "DOC" and e["to_value"] == "SERVICE_CONFIRM"),
                         "báo xong dịch vụ")

    if "đối chiếu" in ten:
        # Khánh 14/10: kỳ đối chiếu của mọi dịch vụ chỉ bắt đầu khi dịch vụ THỰC TẾ
        # hoàn tất. Ngày dự kiến, ngày tạo job và ngày nhập giá không phải mốc.
        if st.startswith("CUS"):
            if st == "CUS_CO":
                return xong_dv()  # làm C/O không có tờ khai/thông quan
            t, nguon = thong_quan()
            return (t, nguon) if t else xong_dv()
        if st.startswith(("WHS", "SVC", "LIFT")):
            return xong_dv()
        return giao()
    if st.startswith("CUS") and st != "CUS_CO" and (buoc["buoc"] == 1 or ten.startswith("thông quan")):
        # 16/10 Khánh: tờ khai phần lớn về qua mail, Sen tự đọc + gán ⇒ KHÔNG tính từ lúc nhận lô / tạo job.
        # Mốc = giờ thông quan in trên tờ khai (cleared_at); chưa có ⇒ bước chưa bắt đầu tính.
        t = _ts(svc.get("cleared_at")) if not _rong(svc.get("cleared_at")) else None
        return (t, "giờ thông quan trên tờ khai") if t else (None, None)
    if buoc["buoc"] == 1:
        return nhan_lo()
    if ten.startswith("thông quan"):
        return thong_quan()
    if ten.startswith("thực hiện"):
        return xong_dv()
    if ten.startswith("booking"):
        return van_don()
    if ten.startswith("lấy"):
        return lay_hang()
    if "giá" in ten:
        if st.startswith("SEA") and la_fcl(svc):          # Khánh chốt 12/10: Sea FCL = 1 ngày sau tạo job
            return _dau_tien(evs, lambda e: True, "tạo job (Sea FCL)")
        if st.startswith("CUS"):
            return thong_quan()
        if st.startswith(("WHS", "SVC", "LIFT")):
            return xong_dv()
        return giao()
    return giao()


def la_fcl(svc):
    sd = _sd(svc)
    t = " ".join(str(x or "") for x in (svc.get("cont_type"), sd.get("cont_type"), svc.get("container_no"),
                                         sd.get("loai_hang"), svc.get("cargo_type"))).upper()
    if "LCL" in t or "CFS" in t:
        return False
    return bool(svc.get("container_no") or svc.get("cont_type") or sd.get("cont_type") or "FCL" in t)


def kpi_thuc(b, svc):
    """KPI áp dụng thật cho dịch vụ (đè chỗ file V1 để mở)."""
    k = b.get("kpi") or ""
    if "giá" in b["ten"].lower() and svc["service_type_code"].startswith("SEA") and la_fcl(svc):
        return "D+1"
    return k


def ky_tt(job, svcs):
    for x in [job] + list(svcs):
        v = x.get("ky_thanh_toan") or _sd(x).get("ky_thanh_toan") if isinstance(x, dict) else None
        if not _rong(v):
            return str(v).strip()
    return None



# 14/10 (Khánh): kỳ đối chiếu theo hợp đồng/thoả thuận của TỪNG KHÁCH (customers.ky_doi_chieu).
# Job/dịch vụ không ghi kỳ thì lấy kỳ của khách. Cột chưa tạo (chưa chạy migration) → coi như trống.
_KY_KHACH = {"t": 0, "d": {}}


def ky_khach(client, customer_id):
    import time
    if not customer_id or client is None:
        return None
    if time.time() - _KY_KHACH["t"] > 300:
        try:
            rows = client.table("customers").select("customer_id,ky_doi_chieu").execute().data or []
            _KY_KHACH["d"] = {r["customer_id"]: r.get("ky_doi_chieu") for r in rows}
        except Exception:
            _KY_KHACH["d"] = {}
        _KY_KHACH["t"] = time.time()
    v = _KY_KHACH["d"].get(customer_id)
    return None if _rong(v) else str(v).strip()

def han_ky(ky, T):
    """Hạn đối chiếu theo kỳ thanh toán khách nhập: 'ngày 25' → ngày 25 tháng sau T; còn lại → cuối tháng T."""
    if not T:
        return None
    T = T.astimezone(VN)
    so = re.findall(r"\d{1,2}", ky or "")
    if so and 1 <= int(so[-1]) <= 31:
        d = int(so[-1])   # 14/10: lấy SỐ CUỐI — "26 tháng trước -> 25 tháng này" = chốt ngày 25
        nam, thang = (T.year + (T.month == 12), T.month % 12 + 1) if T.day > d else (T.year, T.month)
        import calendar
        d = min(d, calendar.monthrange(nam, thang)[1])
        return T.replace(year=nam, month=thang, day=d, hour=23, minute=59, second=59)
    return han("30/31", T)


# ── Lịch dự kiến + quy tắc 6h (Khánh chốt 12/10) ──
CAP_NHAT_LICH = dt.timedelta(hours=6)


def _gio(d, t=None):
    """ngày (+giờ) dự kiến → datetime VN. Chỉ có ngày → 23:59 ngày đó (không phạt oan)."""
    if _rong(d):
        return None
    if _rong(t) and len(str(d)) > 10:          # chuỗi gộp "YYYY-MM-DD HH:MM:SS"
        t = str(d)[11:19]
    try:
        dd = dt.date.fromisoformat(str(d)[:10])
    except ValueError:
        return None
    if not _rong(t):
        try:
            hh = dt.time.fromisoformat(str(t)[:8])
            return dt.datetime.combine(dd, hh, VN)
        except ValueError:
            pass
    return dt.datetime.combine(dd, dt.time(23, 59), VN)


def lich_buoc(b, svc, job):
    """(cột lịch, ngày giờ dự kiến hiện tại) của bước — bước nào có lịch dự kiến thì xét quy tắc 6h."""
    ten = b["ten"].lower()
    st = svc["service_type_code"]
    if b["buoc"] == 1 or "giá" in ten or "đối chiếu" in ten or ten.startswith(("thông quan", "thực hiện")):
        return None, None
    if ten.startswith("lấy"):
        return "scheduled", _gio(svc.get("scheduled_date"), svc.get("scheduled_time"))
    if ten.startswith("booking"):
        return "etd", _gio(job.get("etd"))
    if ten.startswith("đã giao") and not _rong(svc.get("delivery_date")):
        # 14/10: bước Đã giao xét theo ngày giao DỰ KIẾN — quá dự kiến 6h chưa giao/chưa đổi lịch → lỗi
        return "delivery_date", _gio(svc.get("delivery_date"))
    if st.startswith(("SEA", "AIR")) and ("đến" in ten or "giao" in ten):
        return "eta", _gio(job.get("eta"))
    if "giao" in ten:
        return "scheduled", _gio(svc.get("scheduled_date"), svc.get("scheduled_time"))
    return None, None


def xet_lich(cot, P_now, T, evs, svc_id, now):
    """Áp quy tắc: lịch dự kiến P mà tới P+6h chưa có thao tác thực tế và chưa đổi lịch → lỗi.
    Trả (lỗi | None, hạn cập nhật lịch hiện tại)."""
    if not cot or not P_now:
        return None, None
    doi = sorted((e for e in evs if e["event_type"] == "LICH" and e.get("field") == cot
                  and (e.get("svc_id") in (svc_id, None))), key=lambda e: e["event_at"])
    # chuỗi lịch theo thời gian: (giờ đặt lịch, ngày giờ dự kiến)
    chuoi = [(_ts(e["event_at"]), _gio(e["to_value"])) for e in doi if _gio(e["to_value"])]
    if not chuoi:
        chuoi = [(None, P_now)]
    for i, (_, P) in enumerate(chuoi):
        han_cn = P + CAP_NHAT_LICH
        doi_tiep = chuoi[i + 1][0] if i + 1 < len(chuoi) else None
        if T and T <= han_cn and (doi_tiep is None or T <= doi_tiep):
            return None, han_cn                      # thao tác thực tế đúng lịch đang có
        moc_xet = min(x for x in (doi_tiep, T, now) if x)
        if moc_xet > han_cn:
            return (f"Quá lịch dự kiến {P.astimezone(VN):%d/%m %H:%M} hơn 6h chưa cập nhật"), han_cn
    return None, chuoi[-1][1] + CAP_NHAT_LICH


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


def _phan_trang(q, size=1000):
    out, off = [], 0
    while True:
        r = q.range(off, off + size - 1).execute().data or []
        out += r
        if len(r) < size:
            return out
        off += size


def tai_nhieu_job(client, job_ids):
    """14/10: tải dữ liệu KPI cho NHIỀU job một lượt (bảng điều hành) — cùng dữ liệu như danh_gia_job,
    để bảng điều hành và trang chi tiết job dùng CHUNG một cách tính, không lệch nhau."""
    ids = sorted({int(i) for i in job_ids})
    pre = {i: {"job": None, "svcs": [], "docs": set(), "costs": [], "evs": [], "ml": []} for i in ids}
    for k in range(0, len(ids), 150):
        ch = ids[k:k + 150]
        for j in client.table("jobs").select("*").in_("job_id", ch).execute().data or []:
            pre[j["job_id"]]["job"] = j
        for x in _phan_trang(client.table("job_services").select("*").in_("job_id", ch)):
            pre[x["job_id"]]["svcs"].append(x)
        for x in _phan_trang(client.table("documents").select("job_id,doc_type").in_("job_id", ch)):
            pre[x["job_id"]]["docs"].add(x["doc_type"])
        for x in _phan_trang(client.table("job_costs").select("job_id,svc_id,buying_amount,selling_amount").in_("job_id", ch)):
            pre[x["job_id"]]["costs"].append(x)
        for x in _phan_trang(client.table("job_events").select("job_id,event_type,field,to_value,svc_id,event_at,actor")
                             .in_("job_id", ch).order("event_at").order("event_id")):
            pre[x["job_id"]]["evs"].append(x)
        try:
            for x in _phan_trang(client.table("job_mail_log").select("job_id,mail_date,event_type,sender")
                                 .in_("job_id", ch).neq("event_type", "OTHER").order("mail_date")):
                pre[x["job_id"]]["ml"].append(x)
        except Exception:
            pass
    return pre


def _bk_cung_hd(client, job, pre=None):
    """Có Debit/bảng kê trên job KHÁC cùng số HĐ VAT đầu ra không (bảng kê tháng tải 1 lần cho cả đợt hoá đơn)."""
    if "_bk_cung_hd" in job:
        return job["_bk_cung_hd"]
    kq = False
    try:
        so = [x.strip() for x in re.split(r"[,;\n]", str(job.get("vat_invoice_no") or "")) if x.strip()]
        ids = set()
        for x in so[:5]:
            for r in client.table("jobs").select("job_id").ilike("vat_invoice_no", f"*{x}*").limit(200).execute().data or []:
                ids.add(r["job_id"])
        ids.discard(job["job_id"])
        if ids:
            kq = bool(client.table("documents").select("id").eq("doc_type", "DEBIT")
                      .in_("job_id", sorted(ids)[:200]).limit(1).execute().data)
    except Exception as e:
        logger.warning(f"[kpi] bang ke cung HD: {e}")
    job["_bk_cung_hd"] = kq
    return kq


def danh_gia_job(client, job_id, pre=None):
    """Kiểm từng dịch vụ × bước: thiếu ô nào, thiếu chứng từ nào, mốc T, hạn.
    pre = dữ liệu đã tải sẵn của job này (từ tai_nhieu_job) — bảng điều hành dùng để khỏi gọi DB từng job."""
    if pre is not None:
        job = dict(pre["job"]) if pre.get("job") else None
        if not job:
            return []
        svcs = [s for s in pre["svcs"] if (s.get("status_code") or "") != "CANCELLED"]
        docs, costs, evs, ml = set(pre["docs"]), pre["costs"], pre["evs"], pre["ml"]
    else:
        job = (client.table("jobs").select("*").eq("job_id", job_id).limit(1).execute().data or [None])[0]
        if not job:
            return []
        svcs = [s for s in (client.table("job_services").select("*").eq("job_id", job_id).execute().data or [])
                if (s.get("status_code") or "") != "CANCELLED"]
        docs = {d["doc_type"] for d in (client.table("documents").select("doc_type").eq("job_id", job_id).execute().data or [])}
        costs = client.table("job_costs").select("svc_id,buying_amount,selling_amount").eq("job_id", job_id).execute().data or []
        evs = client.table("job_events").select("event_type,field,to_value,svc_id,event_at,actor") \
            .eq("job_id", job_id).order("event_at").execute().data or []
        try:   # mail đầu tiên có thông tin lô (bỏ mail loại OTHER) gắn với job
            ml = client.table("job_mail_log").select("mail_date,event_type,sender").eq("job_id", job_id) \
                .neq("event_type", "OTHER").order("mail_date").execute().data or []
        except Exception:
            ml = []
    last = evs[-1] if evs else None
    job["_mails"] = ml or []
    if ml:
        job["_mail_dau"] = {"t": _ts(ml[0]["mail_date"]), "loai": ml[0]["event_type"],
                            "nguoi": (ml[0].get("sender") or "")[:40]}
    ky = ky_tt(job, svcs) or ky_khach(client, job.get("customer_id"))
    out = []
    for svc in svcs:
        tc = TC["dich_vu"].get(svc["service_type_code"]) or {}
        for b in tc.get("buoc", []):
            loi = None
            if b["buoc"] == 1 and "đối chiếu" not in b["ten"].lower():
                # Bước 1 nghiệp vụ = ô tạo job; dịch vụ chưa có quy trình V1 riêng chỉ có bước đối chiếu.
                thieu_o = [c for c in (tc.get("tao_job") or []) if not _co(c, job, svc, costs)]
                for nhom in (tc.get("tao_job_any_of") or []):
                    if svc["service_type_code"] == "WHS_HANDLE" and "package_quantity" in nhom:
                        continue   # Khánh 13/10: bốc xếp tính theo ca, không có số kiện/khối lượng
                    if not any(_co(c, job, svc, costs) for c in nhom):
                        thieu_o.append(" / ".join(nhom))
            else:
                thieu_o = [c for c in b.get("cot", []) if not _co(c, job, svc, costs)]
            can_doc = [t for t in (doc_bat_buoc(x, svc["service_type_code"]) for x in b.get("chung_tu", [])) if t]
            thieu_ct = [t for t in dict.fromkeys(can_doc) if t not in docs]
            if svc["service_type_code"] in ("AIR_IMP", "SEA_IMP") and b["ten"].lower().startswith("booking") \
                    and ({"AWB", "BL"} & docs):
                # 16/10 Khánh: hàng NHẬP đã có AWB/BL ⇒ AWB/BL chính là xác nhận booking + cân của chuyến (booking,
                # phiếu cân do bên nước ngoài làm, 5P không nhận) ⇒ không đòi số/file booking, phiếu cân nữa.
                thieu_o = [c for c in thieu_o if c != "booking_no"]
                thieu_ct = [t for t in thieu_ct if t not in ("BOOKING", "WEIGHT_SLIP")]
            if "đối chiếu" in b["ten"].lower():
                # 14/10 (Khánh): đã có hoá đơn đầu ra + bảng kê thì bước Đối chiếu ĐỦ, không được báo lỗi.
                # - Hoá đơn = số HĐ VAT đầu ra của job (jobs.vat_invoice_no). Invoice thương mại tải ở bước 1
                #   KHÔNG tính là hoá đơn đối chiếu.
                # - Bảng kê = Debit/bảng kê trên job, HOẶC trên job khác cùng số HĐ VAT (bảng kê tải 1 lần cho cả đợt).
                co_hd = not _rong(job.get("vat_invoice_no"))
                co_bk = "DEBIT" in docs or (co_hd and _bk_cung_hd(client, job, pre))
                thieu_ct = [t for t in thieu_ct if t not in ("INVOICE", "DEBIT")]
                if not co_hd and "INVOICE" in can_doc:
                    thieu_ct.append("INVOICE_VAT")
                if not co_bk and "DEBIT" in can_doc:
                    thieu_ct.append("DEBIT")
                # Thiếu kỳ thanh toán: KHÔNG báo lỗi ngay — hạn mặc định cuối tháng (han_ky); chỉ nhắc khi bước chưa đủ.
                if not ky and (thieu_o or thieu_ct):
                    thieu_o.append("ky_thanh_toan")
            T, ten_moc = moc(b, svc, job, svcs, evs)
            kpi_r = kpi_thuc(b, svc)
            # 14/10 (Khánh): hạn riêng từng ô (kpi_cot). CBT bước 3: biển số xe T+12h từ lúc nhập tờ khai.
            # Còn thiếu (hoặc đã đủ) mà chỉ vướng các ô có hạn riêng → hạn bước = hạn dài nhất của các ô đó.
            kc = b.get("kpi_cot") or {}
            if kc and "kỳ khách" not in (b.get("kpi") or "") and all(c in kc for c in thieu_o) \
                    and (thieu_o or any(c in kc for c in b.get("cot", []))):
                ds_kc = thieu_o or [c for c in b.get("cot", []) if c in kc]
                kpi_r = max((kc[c] for c in ds_kc), key=lambda k: han(k, T) or dt.datetime.min.replace(tzinfo=VN))
            out.append({"job_id": job_id, "job_no": job["job_no"], "created_by": job.get("created_by"),
                        "svc_id": svc["svc_id"], "svc_type": svc["service_type_code"],
                        "buoc": b["buoc"], "ten_buoc": b["ten"], "trang_thai": b.get("trang_thai"), "kpi": b.get("kpi"),
                        "thieu_o": thieu_o, "thieu_ct": thieu_ct, "du": not thieu_o and not thieu_ct,
                        "T": T, "ten_moc": ten_moc, "kpi": kpi_r, "loi": loi,
                        "han": (han_ky(ky, T) if "kỳ khách" in (b.get("kpi") or "") else han(kpi_r, T)),
                        "thao_tac_cuoi": last})
    # Lịch dự kiến + bỏ qua bước (Khánh chốt 12/10)
    now = dt.datetime.now(VN)
    for r in out:
        b = {"buoc": r["buoc"], "ten": r["ten_buoc"]}
        svc = next(x for x in svcs if x["svc_id"] == r["svc_id"])
        cot, P = lich_buoc(b, svc, job)
        r["lich_du_kien"] = P
        loi_lich, r["han_cap_nhat_lich"] = xet_lich(cot, P, r["T"], evs, r["svc_id"], now)
        # 16/10 Khánh: lịch đi (ETD) đã có ngày đi THỰC TẾ (ATD đọc từ B/L, AWB, tra giờ bay) khớp lịch (≤ P+6h)
        # ⇒ đúng lịch, không phải lỗi "quá lịch chưa cập nhật".
        if loi_lich and cot == "etd" and not _rong(svc.get("atd")) and P and _ts(svc["atd"]) \
                and _ts(svc["atd"]) <= P + CAP_NHAT_LICH:
            loi_lich = None
        if loi_lich and not r.get("loi") and not r["du"]:   # đã nhập đủ thì không bắt lỗi lịch
            r["loi"] = loi_lich
    # 13/10 (Khánh): job/dịch vụ đã qua bước (theo trạng thái hoặc bước sau đã đủ) mà bước này còn thiếu
    # → LỖI, không được để "Chưa đến". VD: Đã giao mà thiếu ô giao hàng / thiếu giá.
    QUA = {"PENDING": set(), "DRAFT": set(),
           "ASSIGNED": {"Start"}, "DISPATCHED": {"Start"}, "IN_TRANSIT": {"Start"}, "IN_PROGRESS": {"Start"},
           "CUS_APPROVED": {"Start"},
           "DELIVERED": {"Start", "Processing", "Delivered", "Finish"},
           "COMPLETED": {"Start", "Processing", "Delivered", "Finish"}}
    # Khánh 13/10: thông tin được CẬP NHẬT SỚM ở mọi bước (giá tạm tính, ngày giao, biển số, số TK…) ⇒
    # bước sau chỉ coi là "đã xảy ra" khi có thao tác THỰC TẾ: đổi trạng thái dịch vụ/job hoặc tải chứng từ.
    # Bước Giá / Đối chiếu không bao giờ là bằng chứng bước trước đã xảy ra.
    evs_that = [e for e in evs if e["event_type"] in ("STATUS", "SVC_STATUS", "DOC")]

    def _cho_tq(r):
        # 16/10 Khánh: CUS bước Mở tờ khai / Thông quan chỉ tính khi đã có giờ thông quan trên tờ khai
        # (Sen tự đọc tờ khai từ mail). Chưa có ⇒ không báo lỗi bỏ bước / thiếu, chờ tờ khai.
        return (r["svc_type"].startswith("CUS") and r["svc_type"] != "CUS_CO" and r["T"] is None
                and (r["buoc"] == 1 or (r["ten_buoc"] or "").lower().startswith("thông quan")))

    def _xay_ra(x):
        ten = (x["ten_buoc"] or "").lower()
        if "giá" in ten or "đối chiếu" in ten:
            return False
        svc_x = next(v for v in svcs if v["svc_id"] == x["svc_id"])
        T, nguon = moc({"buoc": x["buoc"], "ten": x["ten_buoc"]}, svc_x, job, svcs, evs_that)
        return T is not None and not (nguon or "").startswith("tạo job")

    for sid in {r["svc_id"] for r in out}:
        svc = next(x for x in svcs if x["svc_id"] == sid)
        qua = QUA.get(job.get("status_code") or "", set()) | QUA.get(svc.get("status_code") or "", set())
        ds = sorted((r for r in out if r["svc_id"] == sid), key=lambda r: r["buoc"])
        for i, r in enumerate(ds):
            if r["du"] or r.get("loi") or _cho_tq(r):
                continue
            # Khánh chốt 13/10: bước SAU đã xảy ra (nhập đủ, hoặc có thao tác thực tế: up booking/AWB, gán xe,
            # BBGH...) mà bước NÀY còn thiếu → LỖI ngay, không chờ hết hạn.
            sau_xay_ra = next((x for x in ds[i + 1:] if _xay_ra(x)), None)
            qua_trang_thai = r.get("trang_thai") in qua and not (r["han"] and now <= r["han"])
            if sau_xay_ra or qua_trang_thai:
                thieu = [NHAN.get(x, x) for x in r["thieu_o"]] + [DOC_NHAN.get(x, x) for x in r["thieu_ct"]]
                ly_do = (f"bước {sau_xay_ra['buoc']}. {sau_xay_ra['ten_buoc']} đã xảy ra" if sau_xay_ra
                         else "job đã qua bước này")
                r["loi"] = f"Thiếu thông tin: {ly_do} nhưng bước này chưa nhập đủ" + (f" ({', '.join(thieu)})" if thieu else "")
    for sid in {r["svc_id"] for r in out}:
        ds = sorted((r for r in out if r["svc_id"] == sid), key=lambda r: r["buoc"])
        for i, r in enumerate(ds):
            if r["T"] is None and not r.get("loi") and not _cho_tq(r) and any(_xay_ra(x) for x in ds[i + 1:]):
                r["loi"] = "Bỏ qua bước (bước sau đã có, bước này chưa ghi)"
    # 19/10 (Khánh): bước trước CHƯA XẢY RA thì bước sau không thể lỗi "quá lịch" — VD hàng chưa thông quan
    # thì chưa thể giao ⇒ bước "Đã giao" để Chưa đến. Lỗi chỉ hiện ở bước đầu tiên đang tắc.
    for sid in {r["svc_id"] for r in out}:
        ops = [r for r in sorted((r for r in out if r["svc_id"] == sid), key=lambda r: r["buoc"])
               if not any(k in (r["ten_buoc"] or "").lower() for k in ("giá", "đối chiếu"))]
        for i in range(1, len(ops)):
            r, truoc = ops[i], ops[i - 1]
            if (r.get("loi") or "").startswith("Quá lịch") and not (truoc["du"] or _xay_ra(truoc)):
                r["loi"] = None
    return out


def ghi_buoc_du(client, job_id):
    """Ghi LẦN ĐẦU các bước vừa đủ. Lúc đủ = thời điểm THAO TÁC vừa làm bước đó đủ (không phải lúc quét)."""
    rows = [r for r in danh_gia_job(client, job_id) if r["du"]]
    if not rows:
        return 0
    da = {(x["svc_id"], x["buoc"]) for x in (client.table("job_step_done").select("svc_id,buoc")
                                             .eq("job_id", job_id).execute().data or [])}
    moi = [r for r in rows if (r["svc_id"], r["buoc"]) not in da]
    if not moi:
        return 0
    last = moi[0]["thao_tac_cuoi"] or {}
    client.table("job_step_done").upsert([{
        "job_id": r["job_id"], "svc_id": r["svc_id"], "svc_type": r["svc_type"], "buoc": r["buoc"],
        "ten_buoc": r["ten_buoc"], "trang_thai": r["trang_thai"], "kpi": r["kpi"],
        "done_at": last.get("event_at") or dt.datetime.now(dt.timezone.utc).isoformat(),
        "actor": last.get("actor") or "unknown",
        "moc_t": r["T"].isoformat() if r["T"] else None, "nguon_moc": r["ten_moc"],
    } for r in moi], on_conflict="svc_id,buoc", ignore_duplicates=True).execute()
    return len(moi)


def quet(client, phut=1440):
    """Quét job có thay đổi gần đây (lịch sử sự kiện + dịch vụ sửa)."""
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=phut)).isoformat()
    ids = {e["job_id"] for e in (client.table("job_events").select("job_id").gte("event_at", since).execute().data or [])}
    since_local = (dt.datetime.now() - dt.timedelta(minutes=phut)).isoformat()
    ids |= {s["job_id"] for s in (client.table("job_services").select("job_id").gte("updated_at", since_local).execute().data or [])}
    # Khánh chốt 12/10: KPI chỉ tính job TẠO TỪ lúc đưa lên thật (không tính ngược job cũ)
    import os as _os
    tu = _os.environ.get("KPI_AP_DUNG_TU", "2026-10-12T21:00:00+07:00")   # ngày lên thật
    if tu and ids:
        moi = client.table("jobs").select("job_id").in_("job_id", sorted(ids)).gte("created_at", tu).execute().data or []
        ids = {x["job_id"] for x in moi}
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
                n = quet(get_client(), 15)       # chỉ job có thay đổi 15 phút gần nhất
                if n:
                    logger.info(f"[kpi] ghi {n} bước vừa đủ")
            except Exception as e:
                logger.warning(f"[kpi] quét lỗi: {e}")
            time.sleep(giay)
    threading.Thread(target=chay, daemon=True).start()
