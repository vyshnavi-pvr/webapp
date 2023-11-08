import configparser
from fastapi import FastAPI, Depends, HTTPException
import models
import schemas
import crud
import logging
from passlib.context import CryptContext
from typing import Annotated, List
from fastapi import Depends, FastAPI, HTTPException, Request, responses,status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import psycopg2
from sqlalchemy.orm import Session
from sqlalchemy import and_,create_engine
from passlib.context import CryptContext
from database import DatabaseManager
import csv
import os
import statsd



logging.basicConfig(
    level=logging.INFO,
    format="{asctime} {message}",
    style='{',
    filename='csye6225.log',
    filemode='w'

)

logging.info('application up and running')

stats = statsd.StatsClient('127.0.0.1', 8125,prefix="public")

metric_names = {
    '/healthz': 'HealthCheckHits',
    '/v1/assignments': 'AssignmentsAPIHits',
    # Add more custom metrics for other APIs as needed
}

# Specify the custom metric namespace and dimensions
namespace = 'CSYE6225assignment'
dimensions_base = [{'Name': 'APIName', 'Value': ''}]


class Hasher():
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    def verify_password( plain_password, hashed_password):
        return Hasher.pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash( password):
        return Hasher.pwd_context.hash(password)



# FastAPIApp Class
class FastAPIApp:
    def __init__(self):
        self.app = FastAPI()
        self.database_manager = DatabaseManager()
        self.security = HTTPBasic()
        self.add_routes()
        models.Base.metadata.create_all(bind=self.database_manager.engine)

    def add_routes(self):

        @self.app.on_event("startup")
        async def startup_event():
            self.load_csv_file()

        @self.app.get("/healthz")
        async def health_check():
            stats.incr('health')
            logging.info("Database connection health check pass")
            health_timer = stats.timer('health_timer')
            health_timer.start()
            if self.check_postgres_health():
                health_timer.stop()
                return responses.Response(status_code=200, headers={"cache-control": "no-cache"})

            else:
                health_timer.stop()
                return responses.Response(status_code=503, headers={"cache-control": "no-cache"})


        @self.app.get("/v1/assignments", response_model=list[schemas.AssignmentCreate])
        async def get_all_assignments(
                db: Session = Depends(self.database_manager.get_db),
                current_user: schemas.User = Depends(self.get_current_user)
        ):
            try:
                stats.incr('getall')
                logging.info("getting all assignments of ",current_user.email)
                getall_timer = stats.timer('getall_timer')
                getall_timer.start()
                crud.db_status(self.database_manager)

                
                if current_user is None:
                    raise HTTPException(status_code=401, detail="Authentication failed")

                getall_timer.stop()

                logging.info("getting all assignments of authenticated user with email: ",current_user.email)

                return crud.get_assignments(db, current_user)

            except HTTPException as exc:
                raise exc  

            except Exception as e:
                print(e)
                raise e

        @self.app.get("/v1/assignment", response_model=list[schemas.AssignmentCreate])
        async def get_user_assignments(
                db: Session = Depends(self.database_manager.get_db),
                current_user: schemas.User = Depends(self.get_current_user)):
            try:
                # Check if the user is authenticated
                if current_user is None:
                    raise HTTPException(status_code=401, detail="Authentication failed")

                # Get assignments created by the authenticated user
                user_assignments = crud.get_user_assignments(db, current_user.user_id)
                # Check if there are user assignments
                if not user_assignments:
                    raise HTTPException(status_code=403, detail="No user assignments found")

                return user_assignments

            except HTTPException as exc:
                raise exc  # Re-raise HTTPExceptions to maintain the original status code and detail

            except Exception as e:
                raise HTTPException(status_code=503, detail="Database is not running")
        
        @self.app.post("/v1/assignments", response_model=schemas.AssignmentCreate)
        async def create_assignment(
            assignment: schemas.AssignmentBase,
            db: Session = Depends(self.database_manager.get_db),
            current_user: schemas.User = Depends(self.get_current_user)         
        ):
            try:
                
                if current_user is None:
                    raise HTTPException(status_code=401, detail="Authentication failed")

                
                crud.db_status(self.database_manager)

                
                if not (1 <= assignment.points <= 10) or not (1 <= assignment.num_of_attempts <= 3):
                    raise HTTPException(
                        status_code=400,
                        detail="Points must be between 1 and 10, and num_of_attempts must be between 1 and 3"
                    )

                
                created_assignment = crud.create_user_assignment(db, assignment, current_user.user_id)

                return created_assignment

            except HTTPException as exc:
                raise exc  # Re-raise HTTPExceptions to maintain the original status code and detail

            except Exception as e:
                raise HTTPException(status_code=400, detail="Database is not running")

        @self.app.put("/v1/assignments/{assignment_id}", response_model=schemas.AssignmentCreate)
        async def update_assignment(
            assignment_id: str,
            assignment_update: schemas.AssignmentBase,
            db: Session = Depends(self.database_manager.get_db),
            current_user: schemas.User = Depends(self.get_current_user)
        ):
            try:
                # Check if the user is authenticated
                if current_user is None:
                    raise HTTPException(status_code=401, detail="Authentication failed")

                # Check if the database is running
                crud.db_status(self.database_manager)
                assignment_to_update = crud.get_user_assignment_for_update(db, assignment_id, current_user.user_id)


                # Get the existing assignment
                existing_assignment = crud.get_user_assignments(db, assignment_id)

                # Check if the assignment exists
                if assignment_to_update is None:
                    raise HTTPException(status_code=401, detail="Assignment not found")
                updated_assignment = crud.update_assignment(db, assignment_id, assignment_update)

                return updated_assignment
        
                
            except HTTPException as exc:
                raise exc  # Re-raise HTTPExceptions to maintain the original status code and detail

            except Exception as e:
                print(e)
                raise HTTPException(status_code=503, detail="Database is not running")

        @self.app.delete("/v1/assignments/{assignment_id}", status_code=204)
        async def delete_assignment(
            assignment_id: str,
            db: Session = Depends(self.database_manager.get_db),
            current_user: schemas.User = Depends(self.get_current_user)
        ):
            try:
                # Check if the user is authenticated
                if current_user is None:
                    raise HTTPException(status_code=401, detail="Authentication failed")

                # Check if the database is running
                crud.db_status(self.database_manager)

                # Get the assignment to delete and check if it was created by the user
                assignment_to_delete = crud.get_user_assignment_for_update(db, assignment_id, current_user.user_id)

                # Check if the assignment exists and if it was created by the user
                if assignment_to_delete is None:
                    raise HTTPException(status_code=401, detail="Assignment not found")

                # Delete the assignment
                crud.delete_assignment(db, assignment_to_delete)

            except HTTPException as exc:
                print(exc)
                raise exc  # Re-raise HTTPExceptions to maintain the original status code and detail

            except Exception as e:
                raise HTTPException(status_code=503, detail="Database is not running")




    @staticmethod
    def get_password_hash(self, password):
        return Hasher.pwd_context.hash(password)

    def verify_user(self, db: Session, email: str, password: str):
        try:
            user = db.query(models.User).filter(models.User.email == email).first()
            print(user)
        except Exception as e:
            raise HTTPException(status_code=503, detail="verify_user: Database service is not running")

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
            if os.getenv("CreateAMI") == "true" or os.getenv("CI") == "true":
                conn = psycopg2.connect(
                    dbname=self.database_manager.config.get('DatabaseSection', 'database.dbname'),
                    port=self.database_manager.config.get('DatabaseSection', 'database.port'),
                    user=self.database_manager.config.get('DatabaseSection', 'database.user'),
                    password=self.database_manager.config.get('DatabaseSection', 'database.password'),
                    host=self.database_manager.config.get('DatabaseSection', 'database.host')
                )
            else:
                endpoint= self.database_manager.client.get_secret_value(SecretId="csye2023_db_end_point")['SecretString']
                endpoint= endpoint.split(":")
                conn = psycopg2.connect(
                    dbname=self.database_manager.config.get('DatabaseSection', 'database.dbname'),
                    port=self.database_manager.config.get('DatabaseSection', 'database.port'),
                    user=self.database_manager.client.get_secret_value(SecretId="db_master_user")['SecretString'],
                    password=self.database_manager.client.get_secret_value(SecretId="db_master_pass")['SecretString'],
                    host=endpoint
                
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
