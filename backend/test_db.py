import sqlalchemy
from sqlalchemy import create_engine

pw = "A07180295e%40%40"
ref = "qunzkuxuduqmqyjvtuqf"

urls = [
    f"postgresql://postgres:{pw}@db.{ref}.supabase.co:5432/postgres",
    f"postgresql://postgres.{ref}:{pw}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres",
    f"postgresql://postgres.{ref}:{pw}@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres",
    f"postgresql://postgres.{ref}:{pw}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
]

success_url = None
for url in urls:
    print(f"Trying: {url.replace(pw, '***')}")
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            print(f"SUCCESS!")
            success_url = url
            break
    except Exception as e:
        print(f"FAILED")

if success_url:
    print(f"\nFINAL_URL_FOUND")
else:
    print("\nALL_FAILED")
