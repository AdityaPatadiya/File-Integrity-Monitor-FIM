"""
connection.py
--------------
Handles database connections for both authentication (auth_db)
and File Integrity Monitoring (fim_db) databases using SQLAlchemy ORM.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch database URLs
AUTH_DATABASE_URL = os.getenv("AUTH_DATABASE_URL")
FIM_DATABASE_URL = os.getenv("FIM_DATABASE_URL")

# --- Validate environment variables ---
if not AUTH_DATABASE_URL:
    raise RuntimeError("❌ Missing AUTH_DATABASE_URL in .env file")

if not FIM_DATABASE_URL:
    raise RuntimeError("❌ Missing FIM_DATABASE_URL in .env file")

# --- Create SQLAlchemy engines ---
auth_engine = create_engine(AUTH_DATABASE_URL, echo=False, pool_pre_ping=True)
fim_engine = create_engine(FIM_DATABASE_URL, echo=False, pool_pre_ping=True)

# --- Define separate Base classes for ORM models ---
AuthBase = declarative_base()
FimBase = declarative_base()

# --- Create SessionLocal factories ---
AuthSessionLocal = sessionmaker(bind=auth_engine, autoflush=False, autocommit=False)
FimSessionLocal = sessionmaker(bind=fim_engine, autoflush=False, autocommit=False)

# --- Dependency functions for FastAPI or scripts ---
def get_auth_db():
    """Yields a session connected to the authentication database."""
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_fim_db():
    """Yields a session connected to the FIM database."""
    db = FimSessionLocal()
    try:
        yield db
    finally:
        db.close()
