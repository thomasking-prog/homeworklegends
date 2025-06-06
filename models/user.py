# models/user.py

from sqlalchemy import Column, Integer, Float, String, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class RoleEnum(enum.Enum):
    STUDENT = "student"
    DELEGATE = "delegate"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.STUDENT)

    global_average = Column(Float, nullable=True)

    # Chaque user appartient à une seule classe
    classroom_id = Column(Integer, ForeignKey("classroom.id"), nullable=True)
    classroom = relationship("Classroom", back_populates="users")

    subject_links = relationship("SubjectFollower", back_populates="user")
    subjects = relationship("Subject", secondary="subject_followers", back_populates="followers", viewonly=True)

    rank_points = Column(Float, default=1000)
    rank_id = Column(Integer, ForeignKey("rank.id"), nullable=True)
    rank = relationship("Rank")

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"