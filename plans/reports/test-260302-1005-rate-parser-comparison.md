# Rate Sheet Parser Comparison Report

Generated: 2026-03-02 10:52:51

## Summary

| File | Type | Expected | Regex | DeepSeek | Gemini | Claude |
|------|------|----------|-------|----------|--------|--------|
| trucking_pivot | TRUCKING_DOM | 30 | 30 | 30 | 0 | 30 |
| trucking_vertical | TRUCKING_DOM | 5 | 0 | 5 | 5 | 5 |
| customs | CUSTOMS | 9 | 0 | 9 | 9 | 9 |
| packing | PACKING | 7 | 0 | 7 | 7 | 7 |
| warehouse | WAREHOUSE | 6 | 0 | 6 | 6 | 6 |
| mixed_header | TRUCKING_DOM | 20 | 20 | 20 | 20 | 20 |
| real_ant | TRUCKING_DOM | 54 | 54 | 0 | 56 | 0 |
| real_navf | TRUCKING_DOM | 7 | 7 | 10 | 7 | 7 |
| real_asgl_quotation | PACKING | ? | 0 | 63 | 72 | 57 |
| real_trucking_tuyen_dai | TRUCKING_DOM | ? | 0 | 50 | 23 | 1 |

## Performance

| Metric | Regex | DeepSeek | Gemini | Claude |
|--------|-------|----------|--------|--------|
| Total Time (s) | 0.59 | 659.79 | 93.41 | 141.50 |
| Est. Cost (USD) | $0 | $0.0047 | $0.0041 | $0.1507 |
| Cost/100 files | $0 | $0.05 | $0.04 | $1.51 |

## Detail per File

### trucking_pivot (test_trucking_pivot.xlsx)
- Type: TRUCKING_DOM
- Expected: 30

- **regex**: 30 rates, 0.006s, $0.000000 — OK
  - Hà Nội → Hải Phòng | Truck 1.25T | 1,800,000 VND
  - Hà Nội → Hải Phòng | Truck 2.5T | 2,500,000 VND
  - Hà Nội → Hải Phòng | Truck 5T | 3,500,000 VND
  - ... and 27 more
- **ai_deepseek**: 30 rates, 73.485s, $0.000602 — OK
  - Hà Nội → Hải Phòng | Truck 1.25T | 1,800,000 VND
  - Hà Nội → Hải Phòng | Truck 2.5T | 2,500,000 VND
  - Hà Nội → Hải Phòng | Truck 5T | 3,500,000 VND
  - ... and 27 more
- **ai_gemini**: 0 rates, 1.491s, $0.000157 — OK
- **ai_anthropic**: 30 rates, 17.517s, $0.026400 — OK
  - Hà Nội → Hải Phòng | Truck 1.25T | 1,800,000 VND
  - Hà Nội → Hải Phòng | Truck 2.5T | 2,500,000 VND
  - Hà Nội → Hải Phòng | Truck 5T | 3,500,000 VND
  - ... and 27 more

### trucking_vertical (test_trucking_vertical.xlsx)
- Type: TRUCKING_DOM
- Expected: 5

- **regex**: 0 rates, 0.009s, $0.000000 — OK
- **ai_deepseek**: 5 rates, 13.769s, $0.000252 — OK
  - Hà Nội → Hải Phòng | Truck 5T | 3,500,000 VND
  - Hà Nội → Bắc Ninh | Truck 2.5T | 1,800,000 VND
  - HCM → Bình Dương | CONT 20' | 3,500,000 VND
  - ... and 2 more
- **ai_gemini**: 5 rates, 2.828s, $0.000172 — OK
  - Hà Nội → Hải Phòng | Truck 5T | 3,500,000 VND
  - Hà Nội → Bắc Ninh | Truck 2.5T | 1,800,000 VND
  - HCM → Bình Dương | CONT 20' | 3,500,000 VND
  - ... and 2 more
- **ai_anthropic**: 5 rates, 4.17s, $0.007650 — OK
  - Hà Nội → Hải Phòng | Truck 5T | 3,500,000 VND
  - Hà Nội → Bắc Ninh | Truck 2.5T | 1,800,000 VND
  - HCM → Bình Dương | CONT 20' | 3,500,000 VND
  - ... and 2 more

### customs (test_customs_rates.xlsx)
- Type: CUSTOMS
- Expected: 9

- **regex**: 0 rates, 0.011s, $0.000000 — OK
- **ai_deepseek**: 9 rates, 22.713s, $0.000308 — OK
  - - → - | Khai báo hải quan - Xuất khẩu | 800,000 VND
  - - → - | Khai báo hải quan - Nhập khẩu | 1,000,000 VND
  - - → - | Khai báo hải quan - Tại chỗ | 600,000 VND
  - ... and 6 more
- **ai_gemini**: 9 rates, 3.875s, $0.000233 — OK
  - - → - | Khai báo hải quan - Xuất khẩu | 800,000 VND
  - - → - | Khai báo hải quan - Nhập khẩu | 1,000,000 VND
  - - → - | Khai báo hải quan - Tại chỗ | 600,000 VND
  - ... and 6 more
- **ai_anthropic**: 9 rates, 6.947s, $0.010650 — OK
  - - → - | Khai báo hải quan - Xuất khẩu | 800,000 VND
  - - → - | Khai báo hải quan - Nhập khẩu | 1,000,000 VND
  - - → - | Khai báo hải quan - Tại chỗ | 600,000 VND
  - ... and 6 more

### packing (test_packing_rates.xlsx)
- Type: PACKING
- Expected: 7

- **regex**: 0 rates, 0.006s, $0.000000 — OK
- **ai_deepseek**: 7 rates, 16.666s, $0.000280 — OK
  - - → - | Đóng kiện gỗ | 2,500,000 VND
  - - → - | Đóng kiện gỗ | 3,500,000 VND
  - - → - | Đóng kiện gỗ | 4,500,000 VND
  - ... and 4 more
- **ai_gemini**: 7 rates, 4.138s, $0.000202 — OK
  - - → - | Đóng kiện gỗ < 1 CBM | 2,500,000 VND
  - - → - | Đóng kiện gỗ 1-3 CBM | 3,500,000 VND
  - - → - | Đóng kiện gỗ > 3 CBM | 4,500,000 VND
  - ... and 4 more
- **ai_anthropic**: 7 rates, 4.809s, $0.009150 — OK
  - - → - | Đóng kiện gỗ < 1 CBM | 2,500,000 VND
  - - → - | Đóng kiện gỗ 1-3 CBM | 3,500,000 VND
  - - → - | Đóng kiện gỗ > 3 CBM | 4,500,000 VND
  - ... and 4 more

### warehouse (test_warehouse_rates.xlsx)
- Type: WAREHOUSE
- Expected: 6

- **regex**: 0 rates, 0.106s, $0.000000 — OK
- **ai_deepseek**: 6 rates, 16.997s, $0.000266 — OK
  - - → - | Lưu kho - Hàng thường | 25,000 VND
  - - → - | Lưu kho - Hàng lạnh | 45,000 VND
  - - → - | Lưu kho - Hàng nguy hiểm | 60,000 VND
  - ... and 3 more
- **ai_gemini**: 6 rates, 3.528s, $0.000188 — OK
  - - → - | Lưu kho - Hàng thường | 25,000 VND
  - - → - | Lưu kho - Hàng lạnh | 45,000 VND
  - - → - | Lưu kho - Hàng nguy hiểm | 60,000 VND
  - ... and 3 more
- **ai_anthropic**: 6 rates, 5.127s, $0.008400 — OK
  - - → - | Lưu kho - Hàng thường | 25,000 VND
  - - → - | Lưu kho - Hàng lạnh | 45,000 VND
  - - → - | Lưu kho - Hàng nguy hiểm | 60,000 VND
  - ... and 3 more

### mixed_header (test_mixed_deep_header.xlsx)
- Type: TRUCKING_DOM
- Expected: 20

- **regex**: 20 rates, 0.017s, $0.000000 — OK
  - KCN Quang Minh → Nội Bài | 1.25T | 1,200,000 VND
  - KCN Quang Minh → Nội Bài | 2.5T | 1,800,000 VND
  - KCN Quang Minh → Nội Bài | 5T | 2,500,000 VND
  - ... and 17 more
- **ai_deepseek**: 20 rates, 49.046s, $0.000462 — OK
  - KCN Quang Minh → Nội Bài | 1.25T | 1,200,000 VND
  - KCN Quang Minh → Nội Bài | 2.5T | 1,800,000 VND
  - KCN Quang Minh → Nội Bài | 5T | 2,500,000 VND
  - ... and 17 more
- **ai_gemini**: 20 rates, 7.628s, $0.000397 — OK
  - KCN Quang Minh → Nội Bài | 1.25T | 1,200,000 VND
  - KCN Quang Minh → Nội Bài | 2.5T | 1,800,000 VND
  - KCN Quang Minh → Nội Bài | 5T | 2,500,000 VND
  - ... and 17 more
- **ai_anthropic**: 20 rates, 12.38s, $0.018900 — OK
  - KCN Quang Minh → Nội Bài | 1.25T | 1,200,000 VND
  - KCN Quang Minh → Nội Bài | 2.5T | 1,800,000 VND
  - KCN Quang Minh → Nội Bài | 5T | 2,500,000 VND
  - ... and 17 more

### real_ant (Báo giá ANT.xlsx)
- Type: TRUCKING_DOM
- Expected: 54

- **regex**: 54 rates, 0.03s, $0.000000 — OK
  - AN DƯƠNG, HẢI PHÒNG → CẢNG HẢI PHÒNG | Truck 1.25T | 600,000 VND
  - AN DƯƠNG, HẢI PHÒNG → CẢNG HẢI PHÒNG | Truck 2.5T | 720,000 VND
  - AN DƯƠNG, HẢI PHÒNG → CẢNG HẢI PHÒNG | Truck 3.5T | 840,000 VND
  - ... and 51 more
- **ai_deepseek**: 0 rates, 160.113s, $0.000238 — OK
- **ai_gemini**: 56 rates, 25.51s, $0.000937 — OK
  - AN DƯƠNG, HẢI PHÒNG → CẢNG HẢI PHÒNG | Truck 1.25T | 600,000 VND
  - AN DƯƠNG, HẢI PHÒNG → CẢNG HẢI PHÒNG | Truck 2.5T | 720,000 VND
  - AN DƯƠNG, HẢI PHÒNG → CẢNG HẢI PHÒNG | Truck 3.5T | 840,000 VND
  - ... and 53 more
- **ai_anthropic**: 0 rates, 33.322s, $0.006900 — OK

### real_navf (NAVF_0808.xlsx)
- Type: TRUCKING_DOM
- Expected: 7

- **regex**: 7 rates, 0.043s, $0.000000 — OK
  - Khu công nghiệp Sông Công, Thái Nguyên → Khu công nghiệp Yên Bình, Thái nguyên | 1.25T | 450,000 VND
  - Khu công nghiệp Sông Công, Thái Nguyên → Khu công nghiệp Yên Bình, Thái nguyên | 2.5T | 770,000 VND
  - Khu công nghiệp Sông Công, Thái Nguyên → Khu công nghiệp Yên Bình, Thái nguyên | 3.5T | 880,000 VND
  - ... and 4 more
- **ai_deepseek**: 10 rates, 29.709s, $0.000322 — OK
  - Khu công nghiệp Sông Công, Thái Nguyên → Khu công nghiệp Yên Bình, Thái nguyên | 1.25T | 450,000 VND
  - Khu công nghiệp Sông Công, Thái Nguyên → Khu công nghiệp Yên Bình, Thái nguyên | 2.5T | 770,000 VND
  - Khu công nghiệp Sông Công, Thái Nguyên → Khu công nghiệp Yên Bình, Thái nguyên | 3.5T | 880,000 VND
  - ... and 7 more
- **ai_gemini**: 7 rates, 4.018s, $0.000202 — OK
  - Khu công nghiệp Sông Công, Thái Nguyên → Khu công nghiệp Yên Bình, Thái nguyên | 1.25T | 450,000 VND
  - Khu công nghiệp Sông Công, Thái Nguyên → Khu công nghiệp Yên Bình, Thái nguyên | 2.5T | 770,000 VND
  - Khu công nghiệp Sông Công, Thái Nguyên → Khu công nghiệp Yên Bình, Thái nguyên | 3.5T | 880,000 VND
  - ... and 4 more
- **ai_anthropic**: 7 rates, 6.658s, $0.009150 — OK
  - Khu công nghiệp Sông Công, Thái Nguyên → Khu công nghiệp Yên Bình, Thái nguyên | 1.25T | 450,000 VND
  - Khu công nghiệp Sông Công, Thái Nguyên → Khu công nghiệp Yên Bình, Thái nguyên | 2.5T | 770,000 VND
  - Khu công nghiệp Sông Công, Thái Nguyên → Khu công nghiệp Yên Bình, Thái nguyên | 3.5T | 880,000 VND
  - ... and 4 more

### real_asgl_quotation (ASGL Quotation for shipment 09.01.2026.xlsx)
- Type: PACKING
- Expected: ?

- **regex**: 0 rates, 0.112s, $0.000000 — OK
- **ai_deepseek**: 63 rates, 152.346s, $0.001064 — OK
  - - → - | Wooden box less than 1 CBM | 900,000 VND
  - - → - | Wooden box More than 1 CBM Less than 10 CBM | 900,000 VND
  - - → - | Wooden box more than 10 CBM | 1,078,000 VND
  - ... and 60 more
- **ai_gemini**: 72 rates, 28.028s, $0.001177 — OK
  - - → - | Wooden box less than 1 CBM | 900,000 VND
  - - → - | Wooden box More than 1 CBM Less than 10 CBM | 900,000 VND
  - - → - | Wooden box more than 10 CBM | 1,078,000 VND
  - ... and 69 more
- **ai_anthropic**: 57 rates, 42.959s, $0.046650 — OK
  - - → - | Wooden box less than 1 CBM (Net weight less than 5 ton) | 900,000 VND
  - - → - | Wooden box More than 1 CBM Less than 10 CBM (Net weight less than 5 ton) | 900,000 VND
  - - → - | Wooden box more than 10 CBM (Net weight less than 5 ton) | 1,078,000 VND
  - ... and 54 more

### real_trucking_tuyen_dai (TRUCKING TUYẾN DÀI 2026.xlsx)
- Type: TRUCKING_DOM
- Expected: ?

- **regex**: 0 rates, 0.253s, $0.000000 — OK
- **ai_deepseek**: 50 rates, 124.945s, $0.000882 — OK
  - - → - | Trucking chuyến dài | 7 VND
  - TP. HCM → Hà Nội | 20' | 1,500,000 VND
  - TP. HCM → Hà Nội | 40' | 2,500,000 VND
  - ... and 47 more
- **ai_gemini**: 23 rates, 12.362s, $0.000442 — OK
  - - → - | Trucking chuyến dài | 1 VND
  - - → - | Trucking hàng biển | 1 VND
  - - → - | Trucking tuyến ngắn ngoài Meiko | 1 VND
  - ... and 20 more
- **ai_anthropic**: 1 rates, 7.613s, $0.006900 — OK
  - - → - | Trucking chuyến dài | 7 VND

## Recommendations

1. **Regex parser**: Best for standard trucking pivot tables (fast, free)
2. **DeepSeek**: Best cost/accuracy ratio for AI fallback
3. **Gemini**: Good accuracy, lowest AI cost
4. **Claude**: Highest accuracy but 20-50x more expensive than DeepSeek/Gemini

### Suggested Strategy
- Use regex as primary parser (handles ~70% of trucking files)
- Fall back to DeepSeek for unrecognized formats (best value)
- Consider Gemini for high-volume batch imports (cheapest AI)