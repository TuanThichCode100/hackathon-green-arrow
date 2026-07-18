def verify_user(phone: str, password: str):
    if password == "demo":
        return {"id": 1, "name": "Nguyễn Tiến Dũng", "role": "tinh"}
    return None
