"""
SecureBank User Service - VULNERABLE VERSION
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr, ConfigDict
import sqlite3
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SecureBank User Service (Vulnerable)",
    version="0.1.0",
    description="Deliberately vulnerable API for security portfolio"
)

# Database helper
def get_db():
    return sqlite3.connect('users.db')

# VULN: Weak password hashing (MD5)
def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    model_config = ConfigDict(extra='allow')  # VULN: Mass assignment
    email: EmailStr | None = None

# ... rest of your endpoints ...