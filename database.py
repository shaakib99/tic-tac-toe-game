from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import os

load_dotenv()

class DB:
    instance = None
    session = None
    Base = None
    def __init__(self):
        self.engine = create_engine(os.getenv("DB_CONNECTION"))
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()
        self.Base.metadata.create_all(bind=self.engine)

    
    @staticmethod
    def get_instance():
        if DB.instance is None:
            DB.instance = DB()
        return DB.instance
    
    @staticmethod
    def get_db() -> Session:
       return DB.get_instance().SessionLocal()
    
    @staticmethod
    def get_base():
        return DB.get_instance().Base

    @staticmethod
    def close_db_connection():
        db = DB.get_db()
        try:
            db.close()
        except:
            pass