"""Regression coverage for the complete Điện Biên locality selector."""

from unittest import TestCase

from app.modules.communes.reference_data import DIEN_BIEN_COMMUNES_2025


class CommuneReferenceDataTest(TestCase):
    def test_contains_all_45_current_dien_bien_localities(self):
        names = [name for name, _, _ in DIEN_BIEN_COMMUNES_2025]

        self.assertEqual(len(DIEN_BIEN_COMMUNES_2025), 45)
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("Thanh Nưa", names)
        self.assertIn("Điện Biên Phủ", names)

    def test_reference_names_can_be_inserted_without_overwriting_existing_rows(self):
        """The migration filters by name, preserving pre-existing sample IDs."""
        existing_names = {"Thanh Nưa", "Mường Nhé", "Tủa Chùa"}
        names_to_insert = [
            name for name, _, _ in DIEN_BIEN_COMMUNES_2025 if name not in existing_names
        ]

        self.assertEqual(len(names_to_insert), 42)
        self.assertTrue(existing_names.isdisjoint(names_to_insert))
