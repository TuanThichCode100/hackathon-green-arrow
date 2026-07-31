"""Resident registry is the authoritative population source for operational views."""

from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.modules.communes.models import Commune, Hamlet  # noqa: F401 - register FK metadata
from app.modules.communes import service as commune_service
from app.modules.notifications.models import Notification  # noqa: F401 - register FK metadata
from app.modules.residents.models import Resident
from app.modules.stats import service as stats_service


class ResidentPopulationProjectionTest(TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add_all([
            Commune(id=1, name="Thanh Nưa", lat=21.4, lng=103.0, population=999),
            Commune(id=2, name="Mường Nhé", lat=22.2, lng=102.4, population=999),
            Resident(commune_id=1, name="Người dân 1", phone="0900000001", ethnic="Kinh", literate=True),
            Resident(commune_id=1, name="Người dân 2", phone="0900000002", ethnic="Thái", literate=True),
            Resident(commune_id=2, name="Người dân 3", phone="0900000003", ethnic="Mông", literate=False),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_commune_population_and_overview_are_projected_from_residents(self):
        communes = {item["id"]: item for item in commune_service.list_communes(self.db)}
        overview = stats_service.calc_overview(self.db, "today")

        self.assertEqual(communes[1]["population"], 2)
        self.assertEqual(communes[2]["population"], 1)
        self.assertEqual(overview["total_pop"], 3)
        self.assertIsNone(overview["recv_rate"])
        self.assertIsNone(overview["not_responded"])
