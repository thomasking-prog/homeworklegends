# models/join_request.py

from sqlalchemy import Column, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from models.user import Base
import enum

class RequestStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class JoinRequest(Base):
    __tablename__ = "join_request"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classroom.id"), nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)

    user = relationship("User")
    classroom = relationship("Classroom")