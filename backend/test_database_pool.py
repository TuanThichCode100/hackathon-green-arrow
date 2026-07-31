from unittest import TestCase

from app.core.config import settings
from app.core.database import engine


class DatabasePoolTest(TestCase):
    def test_non_sqlite_connections_validate_before_reuse(self):
        if settings.DATABASE_URL.startswith("sqlite"):
            self.skipTest("SQLite does not use the production connection pool")

        self.assertTrue(engine.pool._pre_ping)
        self.assertEqual(engine.pool._recycle, 1800)
