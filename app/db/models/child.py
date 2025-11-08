from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Child(Base):
    __tablename__ = "children"
    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    parent_id = Column(Integer, ForeignKey("parents.id"), nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    school = Column(String, nullable=True)
    class_name = Column(String, nullable=True)
    temperament = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="child_profile", uselist=False)
    parent = relationship("Parent", backref="children")