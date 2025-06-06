# models/homework.py

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from models.user import Base
import enum

class PriorityEnum(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Homework(Base):
    __tablename__ = "homework"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    due_date = Column(Date, nullable=False)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.MEDIUM)

    # Nouvelle colonne : note facultative sur 20
    grade = Column(Float, nullable=True)

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subject.id"), nullable=False)

    user = relationship("User")
    subject = relationship("Subject")