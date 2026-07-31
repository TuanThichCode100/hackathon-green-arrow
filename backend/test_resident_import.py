"""Regression coverage for resident CSV import outcomes."""

from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.modules.communes.models import Commune  # noqa: F401 - registers residents' FK target
from app.modules.residents import service
from app.modules.residents.models import Resident
from app.modules.residents.schemas import ResidentUpdate


class ResidentImportTest(TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add(
            Resident(
                commune_id=1,
                name="Bản ghi đã có",
                phone="0912345678",
                ethnic="Kinh",
                literate=True,
            )
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_imports_valid_rows_and_reports_duplicate_rows(self):
        result = service.import_residents(
            self.db,
            [
                {"source_row": 2, "commune_id": 1, "name": "Lò Văn Hùng", "phone": "0987654321", "ethnic": "Thái", "literate": True},
                {"source_row": 3, "commune_id": 1, "name": "Số đã tồn tại", "phone": "0912345678", "ethnic": "Kinh", "literate": True},
                {"source_row": 4, "commune_id": 1, "name": "Trùng trong tệp", "phone": "0987654321", "ethnic": "Mông", "literate": False},
            ],
        )

        self.assertEqual(result["imported"], 1)
        self.assertEqual(result["skipped"], 2)
        self.assertEqual(
            result["errors"],
            [
                {"row": 3, "reason": "Số điện thoại đã tồn tại trong danh sách dân cư."},
                {"row": 4, "reason": "Số điện thoại bị trùng trong tệp CSV."},
            ],
        )

    def test_commune_scope_hides_a_resident_from_another_commune(self):
        resident = Resident(
            commune_id=2,
            name="Người dân xã khác",
            phone="0901234567",
            ethnic="Kinh",
            literate=True,
        )
        self.db.add(resident)
        self.db.commit()

        updated = service.update_resident(
            self.db,
            resident.id,
            ResidentUpdate(name="Không được phép sửa"),
            commune_id=1,
        )
        deleted = service.delete_resident(self.db, resident.id, commune_id=1)

        self.assertIsNone(updated)
        self.assertFalse(deleted)
        self.assertEqual(service.get_resident(self.db, resident.id).name, "Người dân xã khác")
