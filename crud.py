# Utils for CRUD
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import models, schemas
from database import DatabaseManager



# def get_users(db: Session):
#     return db.query(models.User).all



def get_assignments(db: Session,current_user: schemas.User):
    print(current_user.user_id)
    return db.query(models.Assignment).all()

def get_user_assignments(db: Session, user_id: str):
    return db.query(models.Assignment).filter(models.Assignment.u_id == user_id).all()
    # return  db.query(schemas.AssignmentUpdate).filter(models.Assignment.users.email == user_id).first()

def create_user_assignment(db: Session, assignment: schemas.AssignmentCreate, user_id: str):
    a_id=str(uuid4())
    db_assignment = models.Assignment(assignment_id = a_id,
        name=assignment.name,
        points=assignment.points,
        num_of_attempts=assignment.num_of_attempts,
        deadline=assignment.deadline,u_id=user_id)
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
   
    a= db.query(models.Assignment).filter(models.Assignment.assignment_id== db_assignment.assignment_id).first()
    print(a)
    return a

def update_assignment(db: Session, assignment_id: str, assignment_update: schemas.AssignmentUpdate):
    # Retrieve the assignment to update
    assignment = db.query(models.Assignment).filter(models.Assignment.assignment_id == assignment_id).first()

    # Check if the assignment exists
    if assignment is None:
        return None  # Or raise an HTTPException if you prefer

    # Update the assignment fields with the new values
    assignment.name = assignment_update.name
    assignment.points = assignment_update.points
    assignment.num_of_attempts = assignment_update.num_of_attempts
    assignment.deadline = assignment_update.deadline

    # Commit the changes to the database
    db.commit()


    return db.query(models.Assignment).filter(models.Assignment.assignment_id == assignment_id).first()

def get_user_assignment_for_update(db: Session, assignment_id: str, user_id: str):
    # Retrieve the assignment by assignment_id and user_id
    assignment = db.query(models.Assignment).filter(
        models.Assignment.assignment_id == assignment_id,
        models.Assignment.u_id == user_id
    ).first()

    return assignment if assignment else None


def delete_assignment(db: Session, assignment_to_delete: models.Assignment):
    # Delete the assignment from the database
    db.delete(assignment_to_delete)
    db.commit()

    
def db_status(dbManager):
    try:
        engine = create_engine(dbManager.db_uri)
        with engine.connect():
            return "Database is running"
    except :
        raise HTTPException(status_code=503, detail="Database is not running")
    
def request_has_body(request):
    length = request.headers.get("content-length")
    return length is not None and int(length) > 0