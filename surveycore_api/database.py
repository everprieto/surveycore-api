from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required. Configure in .env file.")

_connect_args = {}

engine = create_engine(DATABASE_URL, echo=False, connect_args=_connect_args)

Session = sessionmaker(bind=engine)

Base = declarative_base()