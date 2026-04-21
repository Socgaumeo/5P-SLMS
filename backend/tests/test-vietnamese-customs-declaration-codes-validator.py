"""
Unit tests for the shared Vietnamese customs codes validator.

Covers:
- Service-type detection (CUS_IMPORT/CUS_EXPORT/CUS trigger; others skip)
- Loai_hinh whitelist validation (reject unknown codes, accept known ones)
- Error payload shape (missing vs invalid distinguished)
- Normalize helper (upper-case, strip)

Run locally:
    cd backend && python -m pytest tests/test-vietnamese-customs-declaration-codes-validator.py -v
"""

import importlib
import os
import sys
import unittest

# Make `app.*` importable when running from backend/
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(HERE)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

customs = importlib.import_module(
    "app.core.vietnamese-customs-declaration-codes-and-validator"
)


class TestIsCustomsService(unittest.TestCase):
    def test_cus_import_is_customs(self):
        self.assertTrue(customs.is_customs_service("CUS_IMPORT"))
        self.assertTrue(customs.is_customs_service("cus_import"))

    def test_cus_export_is_customs(self):
        self.assertTrue(customs.is_customs_service("CUS_EXPORT"))

    def test_plain_cus_is_customs(self):
        self.assertTrue(customs.is_customs_service("CUS"))

    def test_cus_co_is_not_customs(self):
        # Certificate of Origin is NOT a customs declaration — it doesn't need loai_hinh
        self.assertFalse(customs.is_customs_service("CUS_CO"))

    def test_trucking_is_not_customs(self):
        self.assertFalse(customs.is_customs_service("TRUCKING_DOM"))
        self.assertFalse(customs.is_customs_service("SEA_IMP"))
        self.assertFalse(customs.is_customs_service("AIR_EXP"))

    def test_empty_or_none(self):
        self.assertFalse(customs.is_customs_service(""))
        self.assertFalse(customs.is_customs_service(None))


class TestIsValidLoaiHinh(unittest.TestCase):
    def test_common_codes_valid(self):
        for code in ("A11", "A12", "A41", "B11", "B13", "E31", "G14"):
            self.assertTrue(customs.is_valid_loai_hinh(code), f"{code} should be valid")

    def test_lowercase_normalized(self):
        self.assertTrue(customs.is_valid_loai_hinh("a11"))
        self.assertTrue(customs.is_valid_loai_hinh("  a11  "))

    def test_unknown_codes_rejected(self):
        for bad in ("A1", "Z99", "ABC", "11A", "A-11", ""):
            self.assertFalse(customs.is_valid_loai_hinh(bad), f"{bad!r} should be invalid")

    def test_none(self):
        self.assertFalse(customs.is_valid_loai_hinh(None))


class TestNormalizeLoaiHinh(unittest.TestCase):
    def test_uppercase_and_trim(self):
        self.assertEqual(customs.normalize_loai_hinh("  a11 "), "A11")

    def test_none_to_empty(self):
        self.assertEqual(customs.normalize_loai_hinh(None), "")
        self.assertEqual(customs.normalize_loai_hinh(""), "")


class TestValidateLoaiHinhForService(unittest.TestCase):
    def test_non_customs_always_ok(self):
        # Trucking without loai_hinh — OK, validator shouldn't care
        self.assertIsNone(customs.validate_loai_hinh_for_service("TRUCKING_DOM", None))
        self.assertIsNone(customs.validate_loai_hinh_for_service("SEA_IMP", ""))

    def test_customs_with_valid_code_ok(self):
        self.assertIsNone(customs.validate_loai_hinh_for_service("CUS_IMPORT", "A11"))
        self.assertIsNone(customs.validate_loai_hinh_for_service("CUS_EXPORT", "b11"))

    def test_customs_missing_returns_missing_error(self):
        err = customs.validate_loai_hinh_for_service("CUS_IMPORT", None)
        self.assertIsNotNone(err)
        self.assertEqual(err["error"], "missing_loai_hinh")
        self.assertFalse(err["success"])
        self.assertIn("Loại hình", err["message"])
        self.assertTrue(len(err["suggestions"]) >= 10)
        # Shape check: each suggestion has code + label
        for s in err["suggestions"]:
            self.assertIn("code", s)
            self.assertIn("label", s)

    def test_customs_invalid_returns_invalid_error(self):
        err = customs.validate_loai_hinh_for_service("CUS_IMPORT", "XX99")
        self.assertIsNotNone(err)
        self.assertEqual(err["error"], "invalid_loai_hinh")
        self.assertIn("XX99", err["message"])

    def test_empty_string_treated_as_missing(self):
        err = customs.validate_loai_hinh_for_service("CUS_EXPORT", "   ")
        self.assertIsNotNone(err)
        self.assertEqual(err["error"], "missing_loai_hinh")

    def test_cus_co_skips_validation(self):
        # CO (Certificate of Origin) doesn't need loai_hinh
        self.assertIsNone(customs.validate_loai_hinh_for_service("CUS_CO", None))


class TestFormatCodesForPrompt(unittest.TestCase):
    def test_renders_all_codes(self):
        rendered = customs.format_codes_for_prompt()
        for code in customs.CUSTOMS_CODE_LABELS:
            self.assertIn(code, rendered)


if __name__ == "__main__":
    unittest.main()
