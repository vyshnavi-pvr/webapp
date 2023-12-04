# Create SQLAlchemy models from the Base class

from sqlalchemy import MetaData, CheckConstraint, Column, ForeignKey, func, Integer, String, DateTime
from sqlalchemy.dialects.mysql import BINARY
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users_data"
    __table_args__ = {'schema': 'webappdb'}

    user_id = Column(String(36), primary_key=True, index=True,
                     default=lambda: str(uuid.uuid4()))
    first_name = Column(String(45))
    last_name = Column(String(45))
    email = Column(String(50), unique=True, index=True)
    password = Column(String(70))
    account_created = Column(DateTime, default=func.now())
    account_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    assignments = relationship("Assignment", back_populates="users")


class Assignment(Base):
    __tablename__ = "assignment_data"
    __table_args__ = {'schema': 'webappdb'}

    assignment_id = Column(String(36), primary_key=True,
                           index=True, default=str(uuid.uuid4()), unique=True)
    name = Column(String(45), nullable=False)
    points = Column(Integer, CheckConstraint(
        'points>=1 AND points <= 10'), nullable=False)
    num_of_attempts = Column(Integer, CheckConstraint(
        'num_of_attempts>=1 and num_of_attempts<=3'), nullable=False)
    deadline = Column(DateTime, nullable=False)
    assignment_created = Column(DateTime, default=func.now())
    assignment_updated = Column(
        DateTime, default=func.now(), onupdate=func.now())
    u_id = Column(String(36), ForeignKey("webappdb.users_data.user_id"))

    users = relationship("User", back_populates="assignments")
    submissions = relationship(
        "UserAssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")


class UserAssignmentSubmission(Base):
    __tablename__ = "submission_data"
    __table_args__ = {'schema': 'webappdb'}

    id = Column(String(36), primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()), unique=True)
    assignment_id = Column(String(36), ForeignKey(
        "webappdb.assignment_data.assignment_id"), nullable=False)
    student_id = Column(String(36), ForeignKey(
        "webappdb.users_data.user_id"), nullable=False)
 
    submission_url = Column(String(), nullable=False)
    submission_date = Column(DateTime, nullable=False, default=func.now())
    submission_updated = Column(DateTime, onupdate=func.now(), nullable=False)
    attempts = Column(Integer, nullable=False, default=1)

    assignment = relationship("Assignment", back_populates="submissions")
