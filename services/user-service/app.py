"""
SecureBank User Service - VULNERABLE VERSION
DO NOT USE IN PRODUCTION

This service intentionally contains security vulnerabilities.
See docs/vulnerabilities-catalog.md for details.
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, EmailStr, ConfigDict
import sqlite3
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # VULN: Debug mode
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SecureBank User Service (Vulnerable)",
    version="0.1.0",
    description="Deliberately vulnerable API for security portfolio"
)

# VULN: No connection pooling
def get_db():
    return sqlite3.connect('users.db')

# VULN: Weak password hashing (MD5)
def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    
    class Config:
        extra = 'allow'  # VULN: Mass assignment

# Health check endpoint
@app.get('/health')
def health_check():
    return {"status": "healthy", "version": "0.1.0-vulnerable"}

# VULN 1: SQL Injection in login endpoint
@app.post('/api/users/login', tags=["Authentication"])
def login(req: LoginRequest):
    """
    User login endpoint
    
    VULNERABILITY: SQL Injection via string formatting
    CWE-89: Improper Neutralization of Special Elements used in an SQL Command
    CVSS: 9.8 (Critical)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # VULN: Direct string formatting allows SQL injection
    query = f"SELECT id, username, email, is_admin FROM users WHERE username='{req.username}' AND password='{hash_password(req.password)}'"
    
    logger.debug(f"Executing query: {query}")  # VULN: Logging sensitive data
    
    try:
        result = cursor.execute(query).fetchone()
        if result:
            user_id, username, email, is_admin = result
            # VULN: Predictable token (just user_id)
            return {
                "token": str(user_id),
                "user_id": user_id,
                "username": username,
                "is_admin": is_admin
            }
        raise HTTPException(status_code=401, detail="Invalid credentials")
    finally:
        conn.close()

# VULN 2: No rate limiting on registration
@app.post('/api/users/register', tags=["Authentication"])
def register(user: UserCreate):
    """
    User registration endpoint
    
    VULNERABILITY: No rate limiting, weak password policy
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # VULN: No password complexity validation
        # VULN: SQL injection possible here too
        query = f"INSERT INTO users (username, email, password) VALUES ('{user.username}', '{user.email}', '{hash_password(user.password)}')"
        cursor.execute(query)
        conn.commit()
        return {"message": "User created successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()

# VULN 3: IDOR - No authorization check
@app.get('/api/users/{user_id}', tags=["Users"])
def get_user(user_id: int):
    """
    Get user details
    
    VULNERABILITY: Insecure Direct Object Reference (IDOR)
    CWE-639: Authorization Bypass Through User-Controlled Key
    CVSS: 7.5 (High)
    
    Any user can access any other user's data by changing the user_id parameter.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # VULN: SQL injection + IDOR
    query = f"SELECT id, username, email, is_admin, balance FROM users WHERE id={user_id}"
    result = cursor.execute(query).fetchone()
    conn.close()
    
    if result:
        return {
            "id": result[0],
            "username": result[1],
            "email": result[2],
            "is_admin": result[3],
            "balance": result[4]
        }
    raise HTTPException(status_code=404, detail="User not found")

# VULN 4: Mass assignment allows privilege escalation
@app.put('/api/users/{user_id}', tags=["Users"])
def update_user(user_id: int, update: UserUpdate):
    """
    Update user details
    
    VULNERABILITY: Mass Assignment
    CWE-915: Improperly Controlled Modification of Dynamically-Determined Object Attributes
    
    Attacker can add {"is_admin": true} to escalate privileges.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # VULN: Accepts any fields from request body
    update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # VULN: Build dynamic UPDATE from all request fields (mass assignment!)
    set_clause = ", ".join([f"{k}='{v}'" for k, v in update_dict.items()])
    query = f"UPDATE users SET {set_clause} WHERE id={user_id}"
    
    try:
        cursor.execute(query)
        conn.commit()
        conn.close()
        return {"message": "User updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# OpenAPI documentation
@app.get('/docs', include_in_schema=False)
async def get_docs():
    """Redirect to OpenAPI docs"""
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(openapi_url="/openapi.json", title="SecureBank API Docs")

if __name__ == '__main__':
    import uvicorn
    # VULN: Debug mode and accessible from all interfaces
    uvicorn.run(app, host='0.0.0.0', port=8000, reload=True)
    