#https://www.mongodb.com/resources/products/compatibilities/docker

import os #usage of os to connect
from sqlalchemy import create_engine  # type: ignore[import]
from sqlalchemy.orm import sessionmaker, declarative_base  # type: ignore[import]

# Reads specified URL from docker-compose.yaml, otherwise defaults to localhost
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://admin:rafdah@postgres_db:5432/inventory_db"

#reference gathered: https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.sessionmaker
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 
#sessionmaker had to go through pip install SQLAlchemy additionally another import too

Base = declarative_base()

# This is the function for main.py to take too
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()