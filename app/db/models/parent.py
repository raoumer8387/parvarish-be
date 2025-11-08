from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Parent(Base):
    __tablename__ = "parents"
    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    phone = Column(String, nullable=True)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    father_age = Column(Integer, nullable=True)
    mother_age = Column(Integer, nullable=True)
    married_since = Column(Integer, nullable=True)
    is_single_parent = Column(Boolean, nullable=True)

    user = relationship("User", backref="parent_profile", uselist=False)