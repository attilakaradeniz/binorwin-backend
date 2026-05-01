from fastapi import FastAPI
import models
from database import engine

# Create the database tables based on our models
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "BinOrWin API and Database are running perfectly!"}