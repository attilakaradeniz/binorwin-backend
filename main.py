from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import engine, SessionLocal

# Create the database tables based on our models
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get the database session securely per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Root endpoint just to check if the server is alive
@app.get("/")
def read_root():
    return {"message": "BinOrWin API and Database are running perfectly!"}

# Endpoint to create a new post
@app.post("/posts/", response_model=schemas.PostResponse)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    # Create a new Post model instance using the data from the user
    new_post = models.Post(title=post.title, image_url=post.image_url)
    
    # Add the new post to the database session
    db.add(new_post)
    
    # Commit the transaction to save it permanently
    db.commit()
    
    # Refresh the instance to get the newly generated ID
    db.refresh(new_post)
    
    return new_post

# Endpoint to fetch a list of posts
@app.get("/posts/", response_model=list[schemas.PostResponse])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Fetch posts from the database with pagination (skip and limit)
    posts = db.query(models.Post).offset(skip).limit(limit).all()
    return posts

# Endpoint to vote on a specific post
@app.post("/posts/{post_id}/vote", response_model=schemas.PostResponse)
def vote_on_post(post_id: int, vote_type: str, db: Session = Depends(get_db)):
    # Find the post in the database using its ID
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    
    # If the post doesn't exist, return a 404 error
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    # Increment the correct vote counter based on user's action
    if vote_type == "bin":
        post.bin_votes += 1
    elif vote_type == "win":
        post.win_votes += 1
    else:
        raise HTTPException(status_code=400, detail="Invalid vote type. Use 'bin' or 'win'")
        
    # Save the updated post to the database
    db.commit()
    db.refresh(post)
    
    return post

# Endpoint to create a new argument (comment) for a specific post
@app.post("/posts/{post_id}/arguments", response_model=schemas.ArgumentResponse)
def create_argument_for_post(post_id: int, argument: schemas.ArgumentCreate, db: Session = Depends(get_db)):
    # First, verify that the post actually exists
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Verify that the action type is valid
    if argument.action_type not in ["bin", "win"]:
        raise HTTPException(status_code=400, detail="action_type must be either 'bin' or 'win'")

    # Create and save the new argument
    new_argument = models.Argument(
        post_id=post_id,
        action_type=argument.action_type,
        content=argument.content
    )
    
    db.add(new_argument)
    db.commit()
    db.refresh(new_argument)
    
    return new_argument

# Endpoint to fetch all arguments for a specific post
@app.get("/posts/{post_id}/arguments", response_model=list[schemas.ArgumentResponse])
def read_arguments_for_post(post_id: int, db: Session = Depends(get_db)):
    # Query the arguments table filtering by the specific post_id
    arguments = db.query(models.Argument).filter(models.Argument.post_id == post_id).all()
    return arguments