import httpx
from fastapi import Header, HTTPException, Depends, Request

SUPABASE_URL = "https://qunzkuxuduqmqyjvtuqf.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF1bnprdXh1ZHVxbXF5anZ0dXFmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzOTk3NTcsImV4cCI6MjA5OTk3NTc1N30.H1toe-UChtLQE88ZdvsvvyftQ8EBGT8hTlKczFhQAdI"

def verify_supabase_token(token: str):
    try:
        resp = httpx.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={"Authorization": f"Bearer {token}", "apikey": ANON_KEY},
            timeout=5.0
        )
        if resp.status_code == 200:
            user = resp.json()
            return user.get("user_metadata", {}).get("role", "tinh")
    except Exception:
        pass
    return None

def get_current_user_role(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # For Hackathon testing: if no token, allow bypass with default role
        return "tinh"
    
    token = auth_header.split(" ")[1]
    
    # Optional: We could skip verification if it's the mock 'demo' token
    if token == "mock-jwt-token":
        return "tinh"
        
    role = verify_supabase_token(token)
    if role:
        return role
        
    raise HTTPException(status_code=401, detail="Invalid or expired token")

def require_role(allowed_roles: list[str]):
    def role_checker(role: str = Depends(get_current_user_role)):
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden: Insufficient role")
        return role
    return role_checker
