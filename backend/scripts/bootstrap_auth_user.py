"""Grant the first server-managed staff role without editing Supabase Auth JSON manually."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.supabase_client import get_supabase_admin


def find_user(email: str):
    response = get_supabase_admin().auth.admin.list_users()
    users = response if isinstance(response, list) else response.users
    return next((item for item in users if (item.email or "").lower() == email.lower()), None)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap trusted staff access in Supabase Auth")
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", choices=("tinh", "xa"), required=True)
    parser.add_argument("--commune-id", type=int)
    args = parser.parse_args()

    domain = settings.ALLOWED_EMAIL_DOMAIN.strip().lower()
    if not args.email.lower().endswith(f"@{domain}"):
        parser.error(f"Email must use @{domain}")
    if args.role == "xa" and args.commune_id is None:
        parser.error("--commune-id is required for role xa")
    if args.role == "tinh" and args.commune_id is not None:
        parser.error("Cán bộ tỉnh must not have a commune id")

    target = find_user(args.email)
    if not target:
        print("Không tìm thấy tài khoản Supabase Auth có email này.", file=sys.stderr)
        return 2

    app_metadata = target.app_metadata or {}
    app_metadata.update({"role": args.role, "commune_id": args.commune_id})
    get_supabase_admin().auth.admin.update_user_by_id(target.id, {"app_metadata": app_metadata})
    print(f"Đã cấp quyền {args.role} cho {args.email}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
