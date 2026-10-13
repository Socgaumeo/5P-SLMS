"""Bảng điều hành job (Khánh duyệt 13/10/2026).

Mọi user đăng nhập đều xem được để tự sửa phần việc của mình.
Chỉ tính job có NGÀY THỰC HIỆN từ 01/10/2026: dịch vụ có scheduled_date >= 01/10;
dịch vụ chưa có ngày thì lấy ngày tạo job.
Không trả giá / doanh thu / lợi nhuận.
"""
import collections
import datetime as dt
import time
from fastapi import APIRouter, HTTPException, Request

from app.db.supabase_client import get_supabase
from app.api.dependencies import get_current_user_optional

router = APIRouter()
VN = dt.timezone(dt.timedelta(hours=7))
TU_NGAY = "2026-10-01"
MO = ("PENDING", "ASSIGNED", "DISPATCHED", "IN_TRANSIT", "IN_PROGRESS", "DELIVERED")
_cache = {"t": 0, "data": None}


def _ts(s):
    d = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def _all(q, size=1000):
    out, off = [], 0
    while True:
        r = q.range(off, off + size - 1).execute().data or []
        out += r
        if len(r) < size:
            return out
        off += size


def _tinh():
    c = get_supabase()
    now = dt.datetime.now(VN)
    today = now.date().isoformat()
    users = {u["user_id"]: u.get("full_name") or f"user {u['user_id']}"
             for u in c.table("users").select("user_id,full_name").execute().data or []}
    cust = {x["customer_id"]: (x.get("short_name") or x.get("customer_code") or "")
            for x in c.table("customers").select("customer_id,short_name,customer_code").execute().data or []}
    # dịch vụ có ngày thực hiện >= 01/10
    svcs = _all(c.table("job_services").select("job_id,svc_id,service_type_code,status_code,scheduled_date")
                .gte("scheduled_date", TU_NGAY))
    jid = {s["job_id"] for s in svcs}
    # job tạo từ 01/10 có dịch vụ chưa ghi ngày
    moi = _all(c.table("jobs").select("job_id").gte("created_at", TU_NGAY))
    jid |= {j["job_id"] for j in moi}
    jobs, ids = [], sorted(jid)
    for i in range(0, len(ids), 200):
        jobs += c.table("jobs").select("job_id,job_no,status_code,created_by,created_at,customer_id") \
            .in_("job_id", ids[i:i + 200]).execute().data or []
    all_svc = []
    for i in range(0, len(ids), 200):
        all_svc += c.table("job_services").select("job_id,svc_id,service_type_code,status_code,scheduled_date") \
            .in_("job_id", ids[i:i + 200]).execute().data or []
    S = collections.defaultdict(list)
    for s in all_svc:
        S[s["job_id"]].append(s)

    since7 = (now - dt.timedelta(days=7)).isoformat()
    since24 = (now - dt.timedelta(hours=24)).isoformat()
    ev7 = _all(c.table("job_events").select("job_id,to_value,event_at").eq("event_type", "STATUS")
               .eq("to_value", "COMPLETED").gte("event_at", since7))
    xong7_job = {e["job_id"] for e in ev7} & set(ids)
    ev24 = _all(c.table("job_events").select("actor,job_id").gte("event_at", since24))
    sd = _all(c.table("job_step_done").select("job_id,actor,done_at"))

    nv = collections.defaultdict(collections.Counter)
    att = []
    J = {j["job_id"]: j for j in jobs}
    for j in jobs:
        u = users.get(j["created_by"], "(chưa rõ)")
        if j["job_id"] in xong7_job:
            nv[u]["xong7"] += 1
        if j["status_code"] not in MO:
            continue
        nv[u]["mo"] += 1
        nv[u][j["status_code"]] += 1
        ss = S[j["job_id"]]
        qua = [s for s in ss if s.get("scheduled_date") and s["scheduled_date"] < today
               and (s["status_code"] or "") not in ("DELIVERED", "COMPLETED", "CANCELLED")]
        tuoi = (now - _ts(j["created_at"])).days
        if qua:
            nv[u]["qua_lich"] += 1
        if tuoi > 14:
            nv[u]["cu_14"] += 1
        if qua or tuoi > 14:
            att.append({"job_id": j["job_id"], "job_no": j["job_no"], "nguoi": u, "uid": j["created_by"],
                        "khach": cust.get(j["customer_id"], ""), "trang_thai": j["status_code"], "tuoi": tuoi,
                        "qua_lich": len(qua),
                        "dich_vu": [{"loai": s["service_type_code"], "tt": s["status_code"],
                                     "ngay": s.get("scheduled_date")} for s in ss]})

    def kenh(a):
        a = a or "unknown"
        if a.startswith("auto|"):
            return "tu_dong"
        return a.split("|")[1] if "|" in a else "unknown"
    tt24 = collections.Counter()
    for e in ev24:
        a = e.get("actor") or ""
        if "|" in a and a.split("|")[0].isdigit():
            tt24[users.get(int(a.split("|")[0]), a)] += 1
    buoc_nv = collections.Counter()
    for d in sd:
        a = d.get("actor") or ""
        if "|" in a and a.split("|")[0].isdigit() and d["job_id"] in J:
            buoc_nv[users.get(int(a.split("|")[0]), a)] += 1

    uid_ten = {v: k for k, v in users.items()}
    nhan_vien = sorted([{"ten": k, "uid": uid_ten.get(k), **dict(v), "thao_tac_24h": tt24.get(k, 0),
                         "buoc_du": buoc_nv.get(k, 0)} for k, v in nv.items() if v.get("mo") or v.get("xong7")],
                       key=lambda x: -x.get("mo", 0))
    theo_tt = collections.Counter(j["status_code"] for j in jobs if j["status_code"] in MO)
    return {
        "gio": now.strftime("%H:%M %d/%m/%Y"), "tu_ngay": TU_NGAY,
        "tong_mo": sum(theo_tt.values()), "theo_tt": dict(theo_tt), "xong7": len(xong7_job),
        "n_chu_y": len(att), "nhan_vien": nhan_vien,
        "can_chu_y": sorted(att, key=lambda x: (-x["qua_lich"], -x["tuoi"]))[:150],
        "thao_tac_24h": {"tong": len(ev24), "kenh": dict(collections.Counter(kenh(e.get("actor")) for e in ev24)),
                         "theo_nguoi": dict(tt24)},
    }


@router.get("/api/dieu-hanh")
async def dieu_hanh(request: Request):
    user = await get_current_user_optional(request)
    if not user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    if time.time() - _cache["t"] > 30 or not _cache["data"]:
        _cache["data"], _cache["t"] = _tinh(), time.time()
    return {"success": True, **_cache["data"], "toi": user.get("user_id")}
