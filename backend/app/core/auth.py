from fastapi import Header, HTTPException, Depends

def require_role(allowed_roles: list[str]):
    def role_checker(x_user_role: str = Header("tinh")):
        if x_user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden: Insufficient role")
        return x_user_role
    return role_checker

def get_current_user_role(x_user_role: str = Header("tinh")):
    return x_user_role
