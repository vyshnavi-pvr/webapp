from sqlalchemy import create_engine
from sqlalchemy.schema import CreateSchema
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import database_exists, create_database
import configparser
from passlib.context import CryptContext
import os
import boto3


class DatabaseManager:
    def __init__(self, config_path='db_config.properties'):
        self.config = configparser.ConfigParser()
        script_directory = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(script_directory, config_path)
        self.config.read(config_file)
        #os.environ["CreateAMI"] = "true"
        if os.getenv("CreateAMI") == "true" or os.getenv("CI") == "true" or os.getenv("CSYE") == "true":
            username = self.config.get('DatabaseSection', 'database.user')
            pwd = self.config.get('DatabaseSection', 'database.password')
            endpoint = self.config.get('DatabaseSection', 'database.host')
            print("using config: {pwd} {username} {endpoint}")
        else:
            self.session = boto3.session.Session()
            self.client = self.session.client(
                service_name='secretsmanager',
                region_name="us-east-1"
            )
            username = self.client.get_secret_value(
                SecretId="db_master_user")['SecretString']
            pwd = self.client.get_secret_value(
                SecretId="db_master_pass")['SecretString']
            endpoint = self.client.get_secret_value(
                SecretId="csye2023_db_end_point")['SecretString']

        db_name = self.config.get('DatabaseSection', 'database.dbname')
        port = self.config.get('DatabaseSection', 'database.port')
        self.db_uri = f'postgresql://{username}:{pwd}@{endpoint}:{port}/{db_name}'
        print(self.db_uri)
        self._setup_database()
        self.engine = create_engine(self.db_uri)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def _setup_database(self):
        if not database_exists(self.db_uri):
            create_database(self.db_uri)

        engine_temp = create_engine(self.db_uri)

        schema_name = "webappdb"
        with engine_temp.connect() as connection:
            connection.execute(CreateSchema(schema_name, if_not_exists=True))
            connection.commit()

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
