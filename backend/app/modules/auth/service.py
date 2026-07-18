def verify_user(phone: str, password: str):
    if password == "demo":
        if phone.startswith("09"):
            return {"id": 1, "name": "Nguyễn Tiến Dũng (Tỉnh)", "role": "tinh"}
        elif phone.startswith("08"):
            # Mocking a commune officer (e.g., commune_id 1 is Thanh Hưng)
            return {"id": 2, "name": "Lò Văn Mười (Xã)", "role": "xa", "commune_id": 1}
        else:
            return {"id": 3, "name": "Cán bộ Vô danh", "role": "tinh"}
    return None
