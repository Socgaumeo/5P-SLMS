"""14/10/2026: Khánh yêu cầu bước Đối chiếu cho mọi dịch vụ SLMS."""
import datetime as dt
import unittest

from app.services import kpi_buoc as k


class Result:
    def __init__(self, data):
        self.data = data


class CustomerQuery:
    def __init__(self, period):
        self.period = period

    def select(self, fields):
        return self

    def execute(self):
        return Result([{"customer_id": 32, "ky_doi_chieu": self.period}])


class Client:
    def __init__(self, period="cuối tháng"):
        self.period = period

    def table(self, name):
        assert name == "customers", name  # preloaded data; no extra job queries
        return CustomerQuery(self.period)


def sample(service_type, *, delivered_at=None, docs=("DEBIT",), vat="VAT-123", events=(), status="IN_PROGRESS"):
    job = {"job_id": 1, "job_no": "TEST-1", "customer_id": 32, "created_by": 1,
           "status_code": status, "vat_invoice_no": vat, "etd": "2026-10-14"}
    svc = {"svc_id": 10, "job_id": 1, "service_type_code": service_type,
           "status_code": status, "service_details": {}, "delivered_at": delivered_at}
    return {"job": job, "svcs": [svc], "docs": set(docs), "costs": [], "evs": list(events), "ml": []}


def reconciliation(rows):
    found = [row for row in rows if row["ten_buoc"] == "Đối chiếu, thanh toán"]
    assert len(found) == 1, found
    return found[0]


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        k._KY_KHACH["t"] = 0
        k._KY_KHACH["d"] = {}
        self.client = Client()

    def test_all_service_codes_have_exactly_one_final_step(self):
        self.assertEqual(len(k.TC["dich_vu"]), 32)
        for code, spec in k.TC["dich_vu"].items():
            with self.subTest(service=code):
                steps = spec["buoc"]
                self.assertEqual(sum(s["ten"] == "Đối chiếu, thanh toán" for s in steps), 1)
                self.assertEqual(steps[-1]["ten"], "Đối chiếu, thanh toán")
                self.assertEqual(steps[-1]["kpi"], "theo kỳ khách")
                self.assertEqual(steps[-1]["cot"], ["vat_invoice_no"])

    def test_complete_vat_and_statement_all_codes(self):
        for code in k.TC["dich_vu"]:
            with self.subTest(service=code):
                r = reconciliation(k.danh_gia_job(self.client, 1, sample(code)))
                self.assertTrue(r["du"], (code, r["thieu_o"], r["thieu_ct"]))
                self.assertIsNone(r["loi"])

    def test_commercial_invoice_does_not_replace_vat_invoice(self):
        r = reconciliation(k.danh_gia_job(self.client, 1, sample("CUS_CO", docs=("INVOICE", "DEBIT"), vat=None)))
        self.assertFalse(r["du"])
        self.assertIn("INVOICE_VAT", r["thieu_ct"])

    def test_scheduled_delivery_is_not_the_reconciliation_anchor(self):
        pre = sample("SEA_IMP")
        pre["svcs"][0]["delivery_date"] = "2026-10-14"
        pre["evs"] = [{"event_at": "2026-10-14T09:00:00+07:00", "event_type": "MOC",
                       "field": "delivery_date", "to_value": "2026-10-14", "svc_id": 10, "actor": "user"}]
        r = reconciliation(k.danh_gia_job(self.client, 1, pre))
        self.assertIsNone(r["T"])
        self.assertIsNone(r["han"])

    def test_actual_delivery_starts_customer_period(self):
        r = reconciliation(k.danh_gia_job(self.client, 1,
            sample("AIR_IMP", delivered_at="2026-10-14T10:30:00+07:00")))
        self.assertEqual(r["T"].astimezone(k.VN).hour, 10)
        self.assertEqual(r["han"].astimezone(k.VN).strftime("%Y-%m-%d"), "2026-10-31")

    def test_customs_and_handling_start_on_real_completion(self):
        for code, event in (
            ("CUS_IMPORT", {"event_type": "MOC", "field": "cd_no", "to_value": "123"}),
            ("CUS_CO", {"event_type": "SVC_STATUS", "field": "status_code", "to_value": "COMPLETED"}),
            ("WHS_HANDLE", {"event_type": "SVC_STATUS", "field": "status_code", "to_value": "COMPLETED"}),
            ("SVC_FUMI", {"event_type": "SVC_STATUS", "field": "status_code", "to_value": "COMPLETED"}),
        ):
            with self.subTest(service=code):
                event.update({"event_at": "2026-10-14T11:00:00+07:00", "svc_id": 10, "actor": "user"})
                r = reconciliation(k.danh_gia_job(self.client, 1, sample(code, events=(event,))))
                self.assertEqual(r["T"].astimezone(k.VN).hour, 11)
                self.assertEqual(r["han"].astimezone(k.VN).strftime("%Y-%m-%d"), "2026-10-31")

    def test_cycle_26_to_25(self):
        T = dt.datetime(2026, 10, 27, 9, tzinfo=k.VN)
        self.assertEqual(k.han_ky("26 tháng trước -> 25 tháng này", T).date(), dt.date(2026, 11, 25))


if __name__ == "__main__":
    unittest.main()
