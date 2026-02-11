"""
SLMS AI Prompts - Update Job Extraction
========================================

Prompt template for extracting update job entities.
"""

UPDATE_JOB_EXTRACTION_PROMPT = """Ban la AI assistant cua he thong logistics 5P Vietnam.

**NHIEM VU:** Trich xuat thong tin cap nhat job tu tin nhan.

==============================================================================
DU LIEU CONTEXT
==============================================================================

**Danh sach khach hang:**
{customers_list}

**Danh sach job dang hoat dong:**
{active_jobs}

**Ngay hien tai:** {current_date}

==============================================================================
VI DU TRICH XUAT (Few-shot)
==============================================================================

**Example 1:**
Input: "doi khach hang job TRK-2601-089 sang DRT2"
Output:
```json
{{
    "job_number": "TRK-2601-089",
    "action_type": "change_customer",
    "new_customer_code": "DRT2",
    "confidence": 0.95
}}
```

**Example 2:**
Input: "job 089 sua lai khach thanh Dreamtech"
Output:
```json
{{
    "job_number_partial": "089",
    "action_type": "change_customer",
    "new_customer_code": "Dreamtech",
    "confidence": 0.90
}}
```

**Example 3:**
Input: "them 1 dich vu trucking cho job 085, lay hang o Bac Ninh giao Ha Noi"
Output:
```json
{{
    "job_number_partial": "085",
    "action_type": "add_service",
    "new_service_type": "TRUCKING_SHORT",
    "origin_address": "Bac Ninh",
    "dest_address": "Ha Noi",
    "confidence": 0.90
}}
```

**Example 4:**
Input: "chuyen don DRT sang SEVT"
Output:
```json
{{
    "customer_filter": "DRT",
    "action_type": "change_customer",
    "new_customer_code": "SEVT",
    "confidence": 0.80
}}
```

**Example 5:**
Input: "sua dia chi giao hang job 087 thanh KCN Yen Phong"
Output:
```json
{{
    "job_number_partial": "087",
    "action_type": "update_address",
    "dest_address": "KCN Yen Phong",
    "confidence": 0.85
}}
```

**Example 6:**
Input: "khach yeu cau khong xep chong job TRK-0402-0002"
Output:
```json
{{
    "job_number": "TRK-0402-0002",
    "action_type": "add_note",
    "notes": "Khach yeu cau khong xep chong",
    "confidence": 0.90
}}
```

**Example 7:**
Input: "cho hang tu 8h den 12h TRK-0402-0002"
Output:
```json
{{
    "job_number": "TRK-0402-0002",
    "action_type": "add_note",
    "notes": "Cho hang tu 8h den 12h",
    "confidence": 0.85
}}
```

**Example 8:**
Input: "phi cho gio 500k job 089"
Output:
```json
{{
    "job_number_partial": "089",
    "action_type": "add_fee",
    "fee_type": "SVC_WAITING",
    "fee_amount": 500000,
    "notes": "Phi cho gio",
    "confidence": 0.90
}}
```

**Example 9:**
Input: "them phi huy chuyen 300k cho job 087"
Output:
```json
{{
    "job_number_partial": "087",
    "action_type": "add_fee",
    "fee_type": "SVC_CANCEL_FEE",
    "fee_amount": 300000,
    "notes": "Phi huy chuyen",
    "confidence": 0.90
}}
```

**Example 10 (ADD_COST with quantity and unit price - explicit format):**
Input: "them chi phi dong goi cho hang, so luong 5 cbm, don gia 790000 vnd/cbm job PKG-0204-0003"
Output:
```json
{{
    "job_number": "PKG-0204-0003",
    "action_type": "add_cost",
    "cost_name": "Chi phi dong goi cho hang",
    "cost_qty": 5,
    "cost_unit_price": 790000,
    "cost_unit": "cbm",
    "confidence": 0.95
}}
```

**Example 10b (ADD_COST with compact qty+unit format):**
Input: "chi phi dong goi: 5cbm, 790000 vnd/cbm, vendor inbus job PKG-0204-0003"
Output:
```json
{{
    "job_number": "PKG-0204-0003",
    "action_type": "add_cost",
    "cost_name": "Chi phi dong goi",
    "cost_qty": 5,
    "cost_unit_price": 790000,
    "cost_unit": "cbm",
    "cost_source": "vendor",
    "vendor_name": "inbus",
    "confidence": 0.95
}}
```
Giai thich: "5cbm" -> cost_qty=5, cost_unit="cbm"; "790000 vnd/cbm" -> cost_unit_price=790000

**Example 11 (ADD_COST from vendor with description):**
Input: "them chi phi thue xe nang 3.5T cho job 089 la 5 trieu/ca, vendor HNB"
Output:
```json
{{
    "job_number_partial": "089",
    "action_type": "add_cost",
    "cost_name": "Chi phi thue xe nang 3.5T",
    "cost_qty": 1,
    "cost_unit_price": 5000000,
    "cost_unit": "ca",
    "cost_source": "vendor",
    "vendor_name": "HNB",
    "confidence": 0.95
}}
```

**Example 12 (ADD_COST simple):**
Input: "chi phi job 089 la 800k tu Tam Bao"
Output:
```json
{{
    "job_number_partial": "089",
    "action_type": "add_cost",
    "cost_name": "Chi phi tu Tam Bao",
    "cost_qty": 1,
    "cost_unit_price": 800000,
    "cost_source": "vendor",
    "vendor_name": "Tam Bao",
    "confidence": 0.90
}}
```

**Example 13 (ADD_COST from dinh muc):**
Input: "chi phi chuyen nay theo dinh muc 1.2 trieu job TRK-0402-001"
Output:
```json
{{
    "job_number": "TRK-0402-001",
    "action_type": "add_cost",
    "cost_name": "Chi phi theo dinh muc",
    "cost_qty": 1,
    "cost_unit_price": 1200000,
    "cost_source": "dinh_muc",
    "confidence": 0.90
}}
```

**Example 14 (ADD_REVENUE):**
Input: "doanh thu job 089 la 1.5 trieu"
Output:
```json
{{
    "job_number_partial": "089",
    "action_type": "add_revenue",
    "revenue_name": "Doanh thu dich vu",
    "revenue_qty": 1,
    "revenue_unit_price": 1500000,
    "confidence": 0.90
}}
```

**Example 15 (ADD_COST + ADD_REVENUE):**
Input: "job 085 chi phi boc xep 900k doanh thu 1.3 trieu"
Output:
```json
{{
    "job_number_partial": "085",
    "action_type": "add_cost_revenue",
    "cost_name": "Chi phi boc xep",
    "cost_qty": 1,
    "cost_unit_price": 900000,
    "revenue_name": "Doanh thu dich vu",
    "revenue_qty": 1,
    "revenue_unit_price": 1300000,
    "confidence": 0.95
}}
```

**Example 16 (ADD_COST from Dinh muc trucking):**
Input: "ap dung dinh muc van chuyen tuyen HN-BN xe 5T cho job 090"
Output:
```json
{{
    "job_number_partial": "090",
    "action_type": "add_cost",
    "cost_name": "Chi phi van chuyen HN-BN xe 5T",
    "cost_qty": 1,
    "cost_source": "dinh_muc",
    "route": "HN-BN",
    "vehicle_type": "5T",
    "confidence": 0.85
}}
```

**Example 17 (MULTI_COST - Nhieu chi phi trong 1 tin nhan):**
Input: "PKG-0204-0003
them chi phi thue xe nang 3.5T, vendor HNB, 5 trieu/ca
chi phi dong goi: 5cbm, 790000 vnd/cbm, vendor inbus"
Output:
```json
{{
    "job_number": "PKG-0204-0003",
    "action_type": "multi_cost",
    "costs": [
        {{
            "cost_name": "Chi phi thue xe nang 3.5T",
            "cost_qty": 1,
            "cost_unit_price": 5000000,
            "cost_unit": "ca",
            "vendor_name": "HNB"
        }},
        {{
            "cost_name": "Chi phi dong goi",
            "cost_qty": 5,
            "cost_unit_price": 790000,
            "cost_unit": "cbm",
            "vendor_name": "inbus"
        }}
    ],
    "confidence": 0.95
}}
```

**Example 18 (MULTI - Nhieu doanh thu voi don vi khac nhau):**
Input: "them doanh thu job PKG-0204-0003
Dich vu nang ha: 8 trieu/ca
Dich vu dong goi: 990000 vnd/cbm"
Output:
```json
{{
    "job_number": "PKG-0204-0003",
    "action_type": "multi_cost_revenue",
    "costs": [],
    "revenues": [
        {{
            "revenue_name": "Dich vu nang ha",
            "revenue_qty": 1,
            "revenue_unit_price": 8000000,
            "revenue_unit": "ca"
        }},
        {{
            "revenue_name": "Dich vu dong goi",
            "revenue_qty": 1,
            "revenue_unit_price": 990000,
            "revenue_unit": "cbm"
        }}
    ],
    "confidence": 0.95
}}
```

**Example 19 (MULTI - Chi phi va doanh thu):**
Input: "job 085
chi phi xe nang HNB 5 trieu
chi phi dong goi inbus 3.95 trieu
doanh thu 12 trieu"
Output:
```json
{{
    "job_number_partial": "085",
    "action_type": "multi_cost_revenue",
    "costs": [
        {{
            "cost_name": "Chi phi xe nang",
            "cost_qty": 1,
            "cost_unit_price": 5000000,
            "cost_unit": "ca",
            "vendor_name": "HNB"
        }},
        {{
            "cost_name": "Chi phi dong goi",
            "cost_qty": 1,
            "cost_unit_price": 3950000,
            "cost_unit": "ca",
            "vendor_name": "inbus"
        }}
    ],
    "revenues": [
        {{
            "revenue_name": "Doanh thu dich vu",
            "revenue_qty": 1,
            "revenue_unit_price": 12000000
        }}
    ],
    "confidence": 0.95
}}
```

==============================================================================
QUY TAC TRICH XUAT
==============================================================================

**Job Number:**
- Ma day du: TRK-YYMM-XXX hoac WHS-YYMM-XXX
- Ma rut gon: 3 so cuoi (089, 087, etc.)
- Neu chi co ten KH, dung customer_filter

**Action Type:**
- "change_customer": Doi khach hang
- "add_service": Them dich vu moi
- "update_address": Sua dia chi
- "update_cargo": Sua thong tin hang hoa
- "add_note": Them ghi chu, yeu cau dac biet, chi tiet cho hang
- "add_fee": Them phi phat sinh (phi cho gio, phi huy chuyen, phi phat sinh khac)
- "add_cost": Them 1 chi phi (tu dinh muc hoac vendor)
- "add_revenue": Them 1 doanh thu
- "add_cost_revenue": Them 1 chi phi va 1 doanh thu
- "multi_cost": Them NHIEU chi phi (khi user liet ke nhieu chi phi)
- "multi_cost_revenue": Them NHIEU chi phi va/hoac doanh thu (khi user liet ke nhieu muc)

**Service Type (cho add_service):**
- TRUCKING_SHORT: Van chuyen noi vung
- TRUCKING_LONG: Van chuyen lien tinh
- WHS_STORAGE: Luu kho
- WHS_HANDLE: Boc xep
- SVC_PACK: Dong goi

**Khach hang:**
- Giu nguyen nhu user nhap, khong tu mapping

==============================================================================
TIN NHAN CAN TRICH XUAT
==============================================================================

"{input}"

==============================================================================
OUTPUT (JSON, KHONG giai thich them)
==============================================================================

Tra ve JSON voi cac truong co the co:
- job_number: Ma job day du (TRK-YYMM-XXX)
- job_number_partial: 3 so cuoi cua job
- customer_filter: Ten KH hien tai (de tim job)
- action_type: change_customer | add_service | update_address | update_cargo | add_note | add_fee | add_cost | add_revenue | add_cost_revenue | multi_cost | multi_cost_revenue
- new_customer_code: Ma KH moi (neu doi KH)
- new_service_type: Loai dich vu moi
- origin_address: Dia chi lay hang
- dest_address: Dia chi giao hang
- cargo_type: Loai hang hoa
- package_quantity: So luong
- package_unit: Don vi (kien, pallet, thung...)
- notes: Ghi chu, yeu cau dac biet
- fee_type: Loai phi (SVC_WAITING, SVC_CANCEL_FEE, SVC_OTHER)
- fee_amount: So tien phi (dong)
- change_reason: Ly do thay doi
- cost_name: Ten chi phi (cho add_cost)
- cost_qty: So luong (mac dinh 1)
- cost_unit_price: Don gia (dong)
- cost_unit: Don vi tinh (ca, chuyen, cbm, kg)
- cost_source: Nguon chi phi (dinh_muc | vendor)
- vendor_name: Ten NCC
- revenue_name: Ten doanh thu (cho add_revenue)
- revenue_qty: So luong (mac dinh 1)
- revenue_unit_price: Don gia doanh thu (dong)
- revenue_unit: Don vi doanh thu (ca, chuyen, cbm, kg, etc.)
- costs: Mang chi phi (cho multi_cost, multi_cost_revenue) - moi item co: cost_name, cost_qty, cost_unit_price, cost_unit, vendor_name
- revenues: Mang doanh thu (cho multi_cost_revenue) - moi item co: revenue_name, revenue_qty, revenue_unit_price, revenue_unit
- route: Tuyen duong (VD: HN-BN)
- vehicle_type: Loai xe (1.25T, 2.5T, 5T, etc.)
- confidence: 0.0-1.0

Chi tra ve cac truong co thong tin, KHONG tra ve null.

QUAN TRONG - PHAI DOC KY:
1. Luon trich xuat cost_name tu mo ta chi phi trong tin nhan
2. TACH RIENG cost_qty (so luong) va cost_unit_price (don gia), TUYET DOI KHONG tinh san thanh tien
3. Neu khong co so luong, mac dinh cost_qty = 1
4. Format "Xunit, Y vnd/unit" hoac "X unit, Y/unit":
   - "5cbm, 790000 vnd/cbm" -> cost_qty=5, cost_unit_price=790000, cost_unit="cbm"
   - "3 chuyen, 500k/chuyen" -> cost_qty=3, cost_unit_price=500000, cost_unit="chuyen"
   - "2ca, 1.5 trieu/ca" -> cost_qty=2, cost_unit_price=1500000, cost_unit="ca"
5. "vendor X" hoac "tu X" o cuoi -> vendor_name="X", cost_source="vendor"
6. NEU user gui NHIEU chi phi/doanh thu trong 1 tin nhan:
   - Dung action_type="multi_cost" neu chi co nhieu chi phi
   - Dung action_type="multi_cost_revenue" neu co ca chi phi va doanh thu
   - Tra ve mang "costs" va/hoac "revenues" chua cac object chi phi/doanh thu
   - Moi item trong mang co: cost_name/revenue_name, cost_qty/revenue_qty, cost_unit_price/revenue_unit_price, cost_unit, vendor_name (neu co)
"""
