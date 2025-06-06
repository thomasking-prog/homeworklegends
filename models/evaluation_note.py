# models/evaluation_note.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from models.user import Base

class EvaluationNote(Base):
    __tablename__ = "evaluation_note"

    id = Column(Integer, primary_key=True)
    label = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    coefficient = Column(Float, default=1.0)

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subject.id"), nullable=False)

    user = relationship("User")
    subject = relationship("Subject")