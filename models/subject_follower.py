from sqlalchemy import Column, Integer, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from models.user import Base

class SubjectFollower(Base):
    __tablename__ = "subject_followers"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subject.id"), nullable=False)

    average = Column(Float, nullable=True)

    user = relationship("User", back_populates="subject_links")
    subject = relationship("Subject", back_populates="follower_links")

    __table_args__ = (UniqueConstraint('user_id', 'subject_id'),)