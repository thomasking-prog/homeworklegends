# models/subject.py

from sqlalchemy import Column, Integer, String, Float, Table, ForeignKey
from sqlalchemy.orm import relationship
from models.user import Base, User
class Subject(Base):
    __tablename__ = "subject"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    follower_links = relationship("SubjectFollower", back_populates="subject")
    followers = relationship("User", secondary="subject_followers", back_populates="subjects", viewonly=True)