# Create initial Pydantic schemas
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):

    first_name: str
    last_name: str
    # email: EmailStr
    password: str


class User(UserBase):

    user_id: str
    account_created: datetime
    account_updated: datetime

    class Config:
        orm_mode = True


class AssignmentBase(BaseModel):

    name: str
    points: int = Field(type, minimum=1, maximum=10,
                        example=2, description="number of points")
    num_of_attempts: int = Field(
        type, minimum=1, maximum=3, example=1, description="number of attempts")
    deadline: datetime


class AssignmentUpdate(BaseModel):
    name: str
    user: UserBase
    points: int = Field(type, minimum=1, maximum=10,
                        example=2, description="number of points")
    num_of_attempts: int = Field(
        type, minimum=1, maximum=3, example=1, description="number of attempts")
    deadline: datetime


class AssignmentCreate(AssignmentBase):
    assignment_id: str
    assignment_created: datetime
    assignment_updated: datetime


class Assignment(AssignmentBase):
    u_id: str


class SubmissionBase(BaseModel):
    submission_url: str


class SubmissionResponse(BaseModel):
    id: str
    assignment_id: str
    submission_url: str
    submission_date: datetime
    submission_updated: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
