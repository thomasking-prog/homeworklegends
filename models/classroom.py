from sqlalchemy import Column, Integer, Float, String, ForeignKey
from .user import Base
from sqlalchemy.orm import relationship
from models.rank import Rank  # Assure-toi que Rank est bien importé

class Classroom(Base):
    __tablename__ = "classroom"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    rank_points_avg = Column(Float, nullable=True)

    # Nouveaux champs pour le rang
    rank_id = Column(Integer, ForeignKey("rank.id"), nullable=True)
    rank = relationship("Rank")

    users = relationship("User", back_populates="classroom")
