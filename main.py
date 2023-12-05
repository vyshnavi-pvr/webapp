from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Request, responses
import models
import schemas
import crud
import logging
from passlib.context import CryptContext
from typing import List
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import psycopg2
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import DatabaseManager
import csv
import os
import statsd
import boto3
import requests

stats = statsd.StatsClient('127.0.0.1', 8125, prefix="app")


class Hasher():
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    def verify_password(plain_password, hashed_password):
        return Hasher.pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password):
        return Hasher.pwd_context.hash(password)


# FastAPIApp Class
class FastAPIApp:
    def __init__(self):
        self.app = FastAPI()
        self.database_manager = DatabaseManager()
        self.security = HTTPBasic()
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.INFO)
        handler = logging.FileHandler('csye6225.log')
        handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
        self.log.addHandler(handler)
        self.log.info("Initialized the application")
        self.add_routes()
        models.Base.metadata.create_all(bind=self.database_manager.engine)

    def add_routes(self):

        @self.app.on_event("startup")
        async def startup_event():
            self.log.info("Add users to the app db")
            self.load_csv_file()

        @self.app.get("/healthz")
        async def health_check():
            stats.incr('health')
            health_timer = stats.timer('health_timer')
            health_timer.start()
            if self.check_postgres_health():
                self.log.info("Database connection health check pass")
                health_timer.stop()
                return responses.Response(status_code=200, headers={"cache-control": "no-cache"})

            else:
                self.log.info("Database connection health check failed")
                health_timer.stop()
                return responses.Response(status_code=503, headers={"cache-control": "no-cache"})

        @self.app.get("/v1/assignments", response_model=list[schemas.AssignmentCreate])
        async def get_all_assignments(
                db: Session = Depends(self.database_manager.get_db),
                current_user: schemas.User = Depends(self.get_current_user)
        ):
            try:
                stats.incr('getAllAssignments')
                self.log.info(f"Getting all assignments for user: {current_user.email}")
                getall_timer = stats.timer('getall_timer')
                getall_timer.start()
                crud.db_status(self.database_manager)

                if current_user is None:
                    self.log.info("Authentication failed")
                    raise HTTPException(
                        status_code=401, detail="Authentication failed")

                getall_timer.stop()
                msg = crud.get_assignments(db, current_user)
                self.log.info(f"Retrieved all assignments for authenticated user: {current_user.email}")
                return msg

            except HTTPException as exc:
                self.log.info(f"HTTPException: {exc}")
                raise HTTPException(status_code=403, detail="Forbidden")

            except Exception as e:
                self.log.info(f"An error occurred: {str(e)}")
                raise HTTPException(status_code=503, detail="Database not found")

        @self.app.get("/v1/assignment/{assignment_id}", response_model=schemas.AssignmentCreate)
        async def get_user_assignments(
                assignment_id: str,
                db: Session = Depends(self.database_manager.get_db),
                current_user: schemas.User = Depends(self.get_current_user)):
            try:
                stats.incr('getAssignment')
                # Check if the user is authenticated
                if current_user is None:
                    self.log.info("Authentication failed while getting assignment")
                    raise HTTPException(
                        status_code=401, detail="Authentication failed")

                # Get assignments created by the authenticated user
                user_assignments = crud.get_user_assignments(
                    db, current_user.user_id)
                # Check if there are user assignments
                if not user_assignments:
                    self.log.info("No user assignments found for ",current_user.email)
                    raise HTTPException(
                        status_code=403, detail="No user assignments found")

                self.log.info("User Assignments retrieved for ",current_user.email)
                
                assignment = crud.get_assignment_by_id( db,assignment_id)
                if assignment is None:
                    raise HTTPException(status_code=404, detail="Assignment not found")
                
   
                return assignment
                # return user_assignments
            
            except Exception as e:
                print(e)
                raise HTTPException(
                    status_code=400, detail="Not Found")

        @self.app.post("/v1/assignments", response_model=schemas.AssignmentCreate,status_code=201)
        async def create_assignment(
            assignment: schemas.AssignmentBase,
            db: Session = Depends(self.database_manager.get_db),
            current_user: schemas.User = Depends(self.get_current_user)
        ):
            try:
                stats.incr('createAssignment')

                if current_user is None:
                    self.log.info("Authentication failed for ",current_user.email)
                    raise HTTPException(
                        status_code=401, detail="Authentication failed")

                crud.db_status(self.database_manager)

                if not (1 <= assignment.points <= 10) or not (1 <= assignment.num_of_attempts <= 3):
                    self.log.info("Invalid input data entered by ",current_user.email)
                    raise HTTPException(
                        status_code=400,
                        detail="Points must be between 1 and 10, and num_of_attempts must be between 1 and 3"
                    )

                created_assignment = crud.create_user_assignment(
                    db, assignment, current_user.user_id)
                self.log.info("Assignment created by ", current_user.email)

                return created_assignment

            except HTTPException as exc:
                raise exc

            except Exception as e:
                raise HTTPException(
                    status_code=400, detail="Not Found")

        @self.app.put("/v1/assignments/{assignment_id}",  status_code=204)
        async def update_assignment(
            assignment_id: str,
            assignment_update: schemas.AssignmentBase,
            db: Session = Depends(self.database_manager.get_db),
            current_user: schemas.User = Depends(self.get_current_user)
        ):
            try:
                stats.incr('updateAssignment')
                # Check if the user is authenticated
                if current_user is None:
                    self.log.info("Authentication failed for ",current_user.email)
                    raise HTTPException(
                        status_code=401, detail="Authentication failed")

                # Check if the database is running
                crud.db_status(self.database_manager)
                self.log.info(f'Updating assignment with id : {assignment_id} by {current_user.email}')
                assignment_to_update = crud.get_user_assignment_for_update(
                    db, assignment_id, current_user.user_id)

                # Get the existing assignment
                existing_assignment = crud.get_user_assignments(
                    db, assignment_id)

                # Check if the assignment exists
                if assignment_to_update is None:
                    self.log.info("Assignment not found")
                    raise HTTPException(
                        status_code=403, detail="Assignment not found")
                updated_assignment = crud.update_assignment(
                    db, assignment_id, assignment_update)
                self.log.info("Assignment updated")
                # return 204

                # return updated_assignment

            except HTTPException as exc:
                raise HTTPException(status_code=404, detail="Assignment not found")

            except Exception as e:
                print(e)
                raise HTTPException(
                    status_code=400, detail="Not Found")

        @self.app.delete("/v1/assignments/{assignment_id}", status_code=204)
        async def delete_assignment(
            assignment_id: str,
            db: Session = Depends(self.database_manager.get_db),
            current_user: schemas.User = Depends(self.get_current_user)
        ):
            try:
                stats.incr('deleteAssignment')
                # Check if the user is authenticated
                if current_user is None:
                    self.log.info("Authentication failed for ",current_user.email)
                    raise HTTPException(
                        status_code=401, detail="Authentication failed")

                # Check if the database is running
                crud.db_status(self.database_manager)
                self.log.info(f"Deleting assignment with id: {assignment_id}")

                # Get the assignment to delete and check if it was created by the user
                assignment_to_delete = crud.get_user_assignment_for_update(
                    db, assignment_id, current_user.user_id)
                self.log.info(f"Deleting assignment with id: {assignment_id}")

                # Check if the assignment exists and if it was created by the user
                if assignment_to_delete is None:
                    self.log.info("Assignment not found")
                    raise HTTPException(
                        status_code=404, detail="Assignment not found")

                # Delete the assignment
                crud.delete_assignment(db, assignment_to_delete)
                self.log.info("Assignment deleted")

            except HTTPException as exc:
                self.log.info(f"HTTPException: {exc} while deleting")
                raise exc

            except Exception as e:
                self.log.info(f"An error occurred: {str(e)} while deleting")
                raise HTTPException(
                    status_code=503, detail="Database is not running")

        @self.app.post("/v1/assignments/{assignment_id}/submission", response_model=schemas.SubmissionResponse,status_code=201)
        async def submit_assignment(
            assignment_id: str,
            submissions_update: schemas.SubmissionBase,
            db: Session = Depends(self.database_manager.get_db),
            current_user: schemas.User = Depends(self.get_current_user)
        ):
            sns_client = boto3.client('sns', region_name='us-east-1')
            ssm_client = boto3.client('ssm', region_name='us-east-1')
            try:
                stats.incr('submitAssignment')
                # Check if the user is authenticated
                if current_user is None:
                    self.log.info("Authentication failed for ",
                                  current_user.email)
                    raise HTTPException(
                        status_code=401, detail="Authentication failed")

                # Check if the database is running
                crud.db_status(self.database_manager)
                self.log.info(f'Uploading submission to assignment with id : {assignment_id} by {current_user.email}')

                # Get the assignment from the database
                get_assignment = crud.get_assignment(db, assignment_id)

                # Check if the assignment exists
                if get_assignment is None:
                    self.log.info("Assignment not found")
                    raise HTTPException(
                        status_code=404, detail="Assignment not found")
                # attempt_count= crud.get_user_attempts(db, assignment_id, current_user.user_id)
                elif crud.get_user_attempts(db, assignment_id, current_user.user_id) >= get_assignment.num_of_attempts:
                    return responses.Response(status_code=400, content="You have exceeded the number of attempts for this assignment")
                # Check if the deadline has passed
                elif datetime.now() > get_assignment.deadline:
                    return responses.Response(status_code=400, content="The deadline for this assignment has passed")

                print(submissions_update.submission_url)
                # Check if the submission URL is provided
                if not submissions_update.submission_url or submissions_update.submission_url == "":
                    return responses.Response(status_code=403, content="Submission URL is required")

                # Validate the submission URL by downloading and checking the file
                try:
                    response = requests.head(submissions_update.submission_url)
                    print(response)

                except Exception as e:
                    print(e)
                    return responses.Response(status_code=404, content="Invalid submission URL")

                content_type = response.headers.get('content-type')
                print(content_type)
                if content_type is None or 'text/html' not in content_type:
                    return responses.Response(status_code=404, content="Invalid file format. Only ZIP files are allowed.")

                # Save the submission to the database
                else:

                    created_submission = crud.create_submission(
                        db, submissions_update, assignment_id, current_user.user_id)

                    file_name = submissions_update.submission_url.split(
                        '/')[-1]
                    # buils sns message
                    sns_message = message = f"Assignment submitted and can be located at {assignment_id}/{current_user.user_id}/{crud.get_user_attempts(db, assignment_id, current_user.user_id)} in google buckect by {current_user.email}. Attempts: {crud.get_user_attempts(db, assignment_id, current_user.user_id)} "
                    attributes = {
                        'release_code_file': {
                            'DataType': 'String',
                            'StringValue': submissions_update.submission_url
                        },
                        'user_release': {
                            'DataType': 'String',
                            'StringValue': f'csye-mybucket/{assignment_id}/{current_user.user_id}/{crud.get_user_attempts(db, assignment_id, current_user.user_id)}'
                        },
                        'tag': {
                            'DataType': 'String',
                            'StringValue': file_name
                        },
                        'from_email': {
                            'DataType': 'String',
                            'StringValue': 'no-reply@vyshnavi2024.me'
                        },
                        'to_email': {
                            'DataType': 'String',
                            'StringValue': current_user.email
                        },
                        'submission_id': {
                            'DataType': 'String',
                            'StringValue': created_submission.id
                        }

                    }

                    sns_topic_arn = ssm_client.get_parameter(
                        Name='csye_topic', WithDecryption=False)
                    print("SNS ARN: ", sns_topic_arn.get(
                        'Parameter').get('Value'))
                    response = sns_client.publish(
                        TopicArn=sns_topic_arn.get('Parameter').get('Value'),
                        Message=message,
                        MessageAttributes=attributes
                    )

                    self.log.info("Submission added ")

                    return created_submission

            except Exception as e:
                print(e)
                return responses.Response(status_code=400, content="Not Found")

    @staticmethod
    def get_password_hash(self, password):
        return Hasher.pwd_context.hash(password)

    def verify_user(self, db: Session, email: str, password: str):
        try:
            user = db.query(models.User).filter(
                models.User.email == email).first()
            print(user)
        except Exception as e:
            raise HTTPException(
                status_code=503, detail="verify_user: Database service is not running")

        if user is None:
            return None
        if Hasher.verify_password(password, user.password) is not True:
            return None

        return user
    security = HTTPBasic()

    def get_current_user(self, credentials: HTTPBasicCredentials = Depends(security)):
        db = next(self.database_manager.get_db())
        user = self.verify_user(db, credentials.username, credentials.password)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user

    def check_postgres_health(self):
        try:
            if os.getenv("CreateAMI") == "true" or os.getenv("CI") == "true" or os.getenv("CSYE") == "true":
                conn = psycopg2.connect(
                    dbname=self.database_manager.config.get(
                        'DatabaseSection', 'database.dbname'),
                    port=self.database_manager.config.get(
                        'DatabaseSection', 'database.port'),
                    user=self.database_manager.config.get(
                        'DatabaseSection', 'database.user'),
                    password=self.database_manager.config.get(
                        'DatabaseSection', 'database.password'),
                    host=self.database_manager.config.get(
                        'DatabaseSection', 'database.host')
                )
            else:

                conn = psycopg2.connect(
                    dbname=self.database_manager.config.get(
                        'DatabaseSection', 'database.dbname'),
                    port=self.database_manager.config.get(
                        'DatabaseSection', 'database.port'),
                    user=self.database_manager.client.get_secret_value(
                        SecretId="db_master_user")['SecretString'],
                    password=self.database_manager.client.get_secret_value(
                        SecretId="db_master_pass")['SecretString'],
                    host=self.database_manager.client.get_secret_value(
                        SecretId="csye2023_db_end_point")['SecretString']

                )
            conn.close()
            return True
        except psycopg2.OperationalError:
            return False

    def load_csv_file(self):
        db: Session = self.database_manager.SessionLocal()
        csv_file_path = "users.csv"

        with open(csv_file_path, newline="") as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                user_data = {
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "email": row["email"],
                    "password": Hasher.get_password_hash(row["password"])
                }
                self.create_user(db, user_data)
        db.close()

    def create_user(self, db: Session, user_data: dict):
        existing_users = db.query(models.User).filter(
            and_(
                models.User.first_name == user_data['first_name'],
                models.User.last_name == user_data['last_name'],
                models.User.email == user_data['email']
            )
        ).all()

        if existing_users:
            return existing_users

        new_user = models.User(**user_data)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    def run(self):

        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=8001)


if __name__ == "__main__":
    app_instance = FastAPIApp()
    app_instance.run()
