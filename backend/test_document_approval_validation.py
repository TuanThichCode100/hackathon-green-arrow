from unittest import TestCase

from fastapi import HTTPException

from app.modules.documents.service import validate_approval


class DocumentApprovalValidationTest(TestCase):
    def test_requires_effective_start_date_before_approval(self):
        draft = {
            "document_number": "125/CĐ-TTg", "title": "Văn bản mẫu", "doc_type": "Công điện",
            "issued_by": "Thủ tướng Chính phủ", "issued_date": "2025-08-01",
            "start_date": None, "scope_type": "province", "commune_ids": [],
        }

        with self.assertRaises(HTTPException) as raised:
            validate_approval(draft)

        self.assertEqual(raised.exception.status_code, 422)
        self.assertIn("Hiệu lực từ ngày", raised.exception.detail)
