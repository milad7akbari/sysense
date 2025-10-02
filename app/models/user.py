from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    DateTime,
    func,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "sys_users"

    id = Column(Integer, primary_key=True, index=True)

    phone_number = Column(String(20), unique=True, index=True, nullable=False, comment="Phone number for registration and login")

    first_name = Column(String(100), comment="First name (optional)")
    last_name = Column(String(100), comment="Last name (optional)")

    is_active = Column(Boolean, default=True, nullable=False, comment="Is the account active?")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="Account creation time")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="Last profile update time")
    last_login_at = Column(DateTime(timezone=True), comment="Last successful login time")

    def __repr__(self):
        return f"<User(id={self.id}, phone='{self.phone_number}', active={self.is_active})>"
