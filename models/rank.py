# models/rank.py

from sqlalchemy import Column, Integer, String, Float
from models.user import Base

class Rank(Base):
    __tablename__ = "rank"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    min_points = Column(Float, nullable=False)
    max_points = Column(Float, nullable=True)
    order = Column(Integer, nullable=False)
    color = Column(String, nullable=True, default="#aaaaaa")  # ✅ couleur du rang

    def __repr__(self):
        return f"<Rank(name={self.name}, min_points={self.min_points}, max_points={self.max_points})>"