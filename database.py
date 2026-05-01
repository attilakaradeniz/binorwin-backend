import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Load environment variables from the hidden .env file
load_dotenv()

# Fetch the password securely
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# The connection string for PostgreSQL dynamically using the hidden password
SQLALCHEMY_DATABASE_URL = f"postgresql://binorwin_user:{DB_PASSWORD}@localhost/binorwin_db"

# Create the engine that manages the connection to the database
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a session factory for our database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all our future database models (tables)
Base = declarative_base()