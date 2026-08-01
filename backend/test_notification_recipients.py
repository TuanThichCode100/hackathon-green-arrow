"""Notification recipient tracking is created from the resident registry."""

from unittest import TestCase
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.modules.agent import service as agent_service
from app.modules.agent.models import AgentDecision  # noqa: F401
from app.modules.communes.models import Commune
from app.modules.notifications import service
from app.modules.notifications.models import Notification, NotificationRecipient  # noqa: F401
from app.modules.residents.models import Resident


class NotificationRecipientTest(TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add_all([
            Commune(id=1, name="A", lat=21.0, lng=103.0, population=999),
            Commune(id=2, name="B", lat=22.0, lng=102.0, population=999),
            Resident(commune_id=1, name="One", phone="0900000011", ethnic="Kinh", literate=True),
            Resident(commune_id=1, name="Two", phone="0900000012", ethnic="Thai", preferred_alert_language="hmn", literate=True),
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_creates_one_pending_recipient_per_resident_and_records_receipt(self):
        notification = service.create_notification_with_recipients(
            self.db,
            commune_id=1,
            decision_id=None,
            channel="sms",
            ethnic_language="Kinh",
            content="Test",
        )
        self.db.commit()

        self.assertIsNotNone(notification)
        self.assertEqual(notification.recipient_count, 2)
        self.assertEqual(
            self.db.query(NotificationRecipient).filter_by(notification_id=notification.id).count(), 2
        )

        service.mark_notification_sent(self.db, notification.id)
        service.record_recipient_receipt(self.db, notification.id, 1)
        self.db.commit()

        recipient = self.db.query(NotificationRecipient).filter_by(
            notification_id=notification.id, resident_id=1
        ).one()
        self.assertEqual(recipient.status, "received")
        self.assertIsNotNone(recipient.received_at)

    def test_skips_empty_commune(self):
        notification = service.create_notification_with_recipients(
            self.db,
            commune_id=2,
            decision_id=None,
            channel="sms",
            ethnic_language="Kinh",
            content="Test",
        )
        self.assertIsNone(notification)

    def test_manual_trigger_uses_residents_instead_of_a_fixed_target_count(self):
        agent_service.manual_trigger(
            self.db,
            SimpleNamespace(
                commune_ids=[1, 2],
                disaster_type="flood",
                message="Test",
            ),
        )

        notifications = self.db.query(Notification).order_by(Notification.channel).all()
        self.assertEqual(len(notifications), 6)
        self.assertEqual({notification.recipient_count for notification in notifications}, {1})
        self.assertEqual(
            self.db.query(NotificationRecipient).count(),
            6,
        )
        total, items = service.list_dispatches(self.db)
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["total_residents"], 2)
        self.assertEqual(items[0]["not_notified_residents"], 2)
        self.assertEqual(items[0]["languages"], ["Tiếng Mông", "Tiếng Việt"])
        self.assertIn("waiting_content", items[0]["channels"]["sms"])
