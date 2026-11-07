from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text
from app.db.session import Base

class LoginHistory(Base):
    __tablename__ = "login_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=True)
    identity = Column(String, nullable=True)
    success = Column(Boolean, nullable=False, default=False)
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    session_id = Column(String, nullable=True, index=True)

class UserPresence(Base):
    __tablename__ = "user_presence"
    user_id = Column(String, primary_key=True)
    last_seen = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    session_id = Column(String, nullable=True, index=True)

class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_user_id = Column(String, index=True, nullable=False)
    action = Column(String, nullable=False)
    target_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
