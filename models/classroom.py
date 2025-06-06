# models/classroom.py

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from models.user import Base

class Classroom(Base):
    __tablename__ = "classroom"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    rank_points_avg = Column(Float, nullable=True)

    # Une classe peut avoir plusieurs users
    users = relationship("User", back_populates="classroom")