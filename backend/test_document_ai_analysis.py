"""Tests for the non-blocking, schema-checked document AI adapter."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from app.core.config import settings
from app.modules.documents.service import run_ai_analysis


def fallback():
    return {"draft": {"title": "Từ OCR", "scope_type": "province", "commune_ids": []}}


class DocumentAiAnalysisTest(TestCase):
    def test_missing_configuration_keeps_ocr_draft_and_sets_friendly_message(self):
        with patch.multiple(settings, LLM_BASE_URL="", LLM_API_KEY="", LLM_MODEL=""):
            result = run_ai_analysis("văn bản", fallback())

        self.assertEqual(result["draft"]["title"], "Từ OCR")
        self.assertEqual(result["ai_analysis"]["status"], "unavailable")
        self.assertIn("AI chưa phân tích", result["ai_analysis"]["message"])

    def test_valid_response_is_sanitized_before_merging(self):
        response = SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"choices": [{"message": {"content": '{"title":"  Văn bản mới  ","issued_date":"2026-07-30","llm_summary":"Tóm tắt ngắn"}'}}]},
        )
        with patch.multiple(settings, LLM_BASE_URL="https://router.example/v1", LLM_API_KEY="secret", LLM_MODEL="small-model"), patch("app.modules.documents.service.httpx.post", return_value=response):
            result = run_ai_analysis("văn bản", fallback())

        self.assertEqual(result["draft"]["title"], "Văn bản mới")
        self.assertEqual(result["draft"]["issued_date"], "2026-07-30")
        self.assertEqual(result["ai_analysis"]["status"], "completed")
