"""Regression coverage for trusted Supabase Auth access claims."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from app.modules.users.router import list_users, update_user_role
from app.modules.users.schemas import UserUpdate


class UsersRouterTest(TestCase):
    def test_lists_access_claims_from_app_metadata(self):
        supabase_users = [
            SimpleNamespace(
                id="user-1",
                email="province@dienbien.gov.vn",
                user_metadata={"name": "Cán bộ tỉnh", "role": "xa"},
                app_metadata={"role": "tinh", "commune_id": None},
            )
        ]
        admin_client = SimpleNamespace(auth=SimpleNamespace(admin=SimpleNamespace(list_users=lambda: supabase_users)))

        with patch("app.modules.users.router.get_supabase_admin", return_value=admin_client):
            result = list_users(user={"role": "tinh"})

        self.assertEqual(result["data"][0]["role"], "tinh")
        self.assertIsNone(result["data"][0]["commune_id"])

    def test_assigns_role_and_commune_to_app_metadata(self):
        existing = SimpleNamespace(
            id="user-2",
            email="commune@dienbien.gov.vn",
            user_metadata={"name": "Cán bộ xã"},
            app_metadata={},
        )
        update = SimpleNamespace(user=SimpleNamespace(
            id="user-2",
            email="commune@dienbien.gov.vn",
            user_metadata={"name": "Cán bộ xã"},
            app_metadata={"role": "xa", "commune_id": 1},
        ))
        admin = SimpleNamespace(
            get_user_by_id=lambda _: SimpleNamespace(user=existing),
            update_user_by_id=lambda _, payload: update,
        )
        admin_client = SimpleNamespace(auth=SimpleNamespace(admin=admin))

        with patch("app.modules.users.router.get_supabase_admin", return_value=admin_client):
            result = update_user_role("user-2", UserUpdate(role="xa", commune_id=1), user={"role": "tinh"})

        self.assertEqual(result["data"]["role"], "xa")
        self.assertEqual(result["data"]["commune_id"], 1)
