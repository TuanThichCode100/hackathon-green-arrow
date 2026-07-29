"""Regression coverage for the Supabase Admin users adapter."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from app.modules.users.router import list_users


class ListUsersTest(TestCase):
    def test_accepts_the_current_supabase_list_response(self):
        supabase_users = [
            SimpleNamespace(
                id="user-1",
                email="province@example.com",
                user_metadata={"name": "Cán bộ tỉnh", "role": "tinh", "commune_id": None},
            )
        ]
        admin_client = SimpleNamespace(auth=SimpleNamespace(admin=SimpleNamespace(list_users=lambda: supabase_users)))

        with patch("app.modules.users.router.get_supabase_admin", return_value=admin_client):
            result = list_users(user={"role": "tinh"})

        self.assertEqual(
            result,
            {
                "data": [
                    {
                        "id": "user-1",
                        "email": "province@example.com",
                        "name": "Cán bộ tỉnh",
                        "role": "tinh",
                        "commune_id": None,
                    }
                ]
            },
        )
