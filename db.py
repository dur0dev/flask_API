from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

PG_DBNAME = os.getenv("PG_DBNAME")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")

DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DBNAME}"

engine = create_engine(DATABASE_URL)