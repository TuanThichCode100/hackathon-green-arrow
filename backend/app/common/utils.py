from datetime import datetime

def format_number(n: int) -> str:
    return f"{n:,}".replace(",", ".")

def format_date(dt: datetime) -> str:
    return dt.strftime("%H:%M %d/%m/%Y")
