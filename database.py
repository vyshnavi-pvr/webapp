from sqlalchemy import create_engine
from sqlalchemy.schema import CreateSchema
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import database_exists, create_database
import configparser
from passlib.context import CryptContext

class DatabaseManager:
    def __init__(self, config_path='db_config.properties'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        username = self.config.get('DatabaseSection', 'database.user')
        pwd = self.config.get('DatabaseSection', 'database.password')
        db_name = self.config.get('DatabaseSection', 'database.dbname')
        self.db_uri = f'postgresql://{username}:{pwd}@localhost:5432/{db_name}'
        self._setup_database()
        self.engine = create_engine(self.db_uri)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def _setup_database(self):
        if not database_exists(self.db_uri):
            create_database(self.db_uri)

        engine_temp = create_engine(self.db_uri)

        schema_name = "webappdb"  # adjust this to your desired schema name if different
        with engine_temp.connect() as connection:
            connection.execute(CreateSchema(schema_name, if_not_exists=True))
            connection.commit()




    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
