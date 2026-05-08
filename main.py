from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import timedelta
import models, schemas, auth
from database import engine, SessionLocal
import os
import shutil
import uuid

# create the database tables based on our models
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
# media server setup
os.makedirs("uploads", exist_ok=True)  # Ensure the uploads directory exists
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.mount("/static", StaticFiles(directory="static"), name="static")

# OAuth2 setup: This tells FastAPI where to look for the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Dependency to get the database session securely per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get the current authenticated user from a JWT token
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except Exception:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# --- AUTH ROUTES ---

# Endpoint to register a new user
@app.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Hash the password and save the new user
    hashed_pwd = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, email=user.email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Endpoint to login and get a JWT token
@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Authenticate user
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create and return JWT token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# basic routes

# Root endpoint just to check if the server is alive
@app.get("/")
def read_root():
    return {"message": "BinOrWin API and Database are running perfectly!"}

# Endpoint to create a new post (Protected: Requires Login)
@app.post("/posts/", response_model=schemas.PostResponse)
def create_post(
    post: schemas.PostCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Create a new Post model instance using the data from the user
    # now also assigning the logged-in user as the owner
    new_post = models.Post(title=post.title, image_url=post.image_url, owner_id=current_user.id)
    
    # adding the new post to the database session
    db.add(new_post)
    
    # committing the transaction to save it permanently
    db.commit()
    
    # refreshing the instance to get the newly generated ID
    db.refresh(new_post)
    
    return new_post

# endpoint to fetch a list of posts
@app.get("/posts/", response_model=list[schemas.PostResponse])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Fetch posts from the database with pagination (skip and limit)
    posts = db.query(models.Post).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts

# endpoint to vote on a specific post
# Endpoint to vote on a specific post (Protected: Requires Login)
@app.post("/posts/{post_id}/vote", response_model=schemas.PostResponse)
def vote_on_post(
    post_id: int, 
    vote_type: str, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # require login to vote!
):
    # check if the vote type is valid first
    if vote_type not in ["bin", "win"]:
        raise HTTPException(status_code=400, detail="Invalid vote type. Use 'bin' or 'win'")

    # find the post
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    # check if this user has already voted on this specific post
    existing_vote = db.query(models.Vote).filter(
        models.Vote.post_id == post_id, 
        models.Vote.user_id == current_user.id
    ).first()
    
    if existing_vote:
        # user has voted before. Let's see what they clicked.
        if existing_vote.vote_type == vote_type:
            # toggle: user clicked the same button again. Remove the vote.
            db.delete(existing_vote)
            if vote_type == "bin":
                post.bin_votes -= 1
            else:
                post.win_votes -= 1
        else:
            # switch vote : They changed their mind (e.g., from bin to win)
            existing_vote.vote_type = vote_type
            if vote_type == "bin":
                post.win_votes -= 1
                post.bin_votes += 1
            else:
                post.bin_votes -= 1
                post.win_votes += 1
    else:
        #  user has never voted on this post
        new_vote = models.Vote(post_id=post_id, user_id=current_user.id, vote_type=vote_type)
        db.add(new_vote)
        if vote_type == "bin":
            post.bin_votes += 1
        else:
            post.win_votes += 1
            
    # save all changes to the database
    db.commit()
    db.refresh(post)
    
    return post

# endpoint to create a new argument (comment) for a specific post (Protected: Requires Login)
@app.post("/posts/{post_id}/arguments", response_model=schemas.ArgumentResponse)
def create_argument_for_post(
    post_id: int, 
    argument: schemas.ArgumentCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # first, verify that the post actually exists
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # verifying action type is valid
    if argument.action_type not in ["bin", "win"]:
        raise HTTPException(status_code=400, detail="action_type must be either 'bin' or 'win'")

    # creating and save the new argument
    # now the owner_id from the logged-in user included
    new_argument = models.Argument(
        post_id=post_id,
        action_type=argument.action_type,
        content=argument.content,
        owner_id=current_user.id
    )
    
    db.add(new_argument)

    # increment the argument counter for this post
    post.arguments_count += 1

    db.commit()
    db.refresh(new_argument)
    
    return new_argument

# endpoint to fetch all arguments for a specific post
@app.get("/posts/{post_id}/arguments", response_model=list[schemas.ArgumentResponse])
def read_arguments_for_post(post_id: int, db: Session = Depends(get_db)):
    # query the arguments table filtering by the specific post_id
    arguments = db.query(models.Argument).filter(models.Argument.post_id == post_id).order_by(models.Argument.created_at.desc()).all()
    return arguments

# Endpoint to update (edit) an existing argument (Protected)
@app.put("/arguments/{argument_id}", response_model=schemas.ArgumentResponse)
def update_argument(
    argument_id: int, 
    updated_argument: schemas.ArgumentCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Find the argument in the database
    argument = db.query(models.Argument).filter(models.Argument.id == argument_id).first()
    
    # if it doesn't exist, return 404
    if not argument:
        raise HTTPException(status_code=404, detail="Argument not found")
        
    # 2. SECURITY CHECK: Ensure the logged-in user is the actual owner of this argument
    if argument.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this argument")
        
    # 3. Update the content and save
    argument.content = updated_argument.content
    argument.action_type = updated_argument.action_type
    
    db.commit()
    db.refresh(argument)
    
    return argument

# endpoint to delete an existing argument (Protected)
@app.delete("/arguments/{argument_id}")
def delete_argument(
    argument_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Find the argument
    argument = db.query(models.Argument).filter(models.Argument.id == argument_id).first()
    
    if not argument:
        raise HTTPException(status_code=404, detail="Argument not found")
        
    # 2. SECURITY CHECK: Only the owner can delete their argument
    if argument.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this argument")
    
    post = db.query(models.Post).filter(models.Post.id == argument.post_id).first()
    if post and post.arguments_count > 0:
        post.arguments_count -= 1
        
    # 3. Delete from database
    db.delete(argument)
    db.commit()
    
    return {"message": "Argument successfully deleted"}



# endpoint to delete a post (Hidden Admin Mode)
@app.delete("/posts/{post_id}")
def delete_post(post_id: int, admin_key: str, db: Session = Depends(get_db)):
    # simple security check: Only allow deletion if the correct secret key is provided
    if admin_key != "supersecretdev":
        raise HTTPException(status_code=403, detail="Forbidden: Invalid admin key")
        
    # find the post in the database
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    
    # if the post doesn't exist, return a 404 error
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    # delete the post from the database
    db.delete(post)
    db.commit()
    
    return {"message": f"Post {post_id} has been permanently deleted"}


# Endpoint to like or unlike an argument (Protected)
@app.post("/arguments/{argument_id}/like", response_model=schemas.ArgumentResponse)
def like_argument(
    argument_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Find the argument
    argument = db.query(models.Argument).filter(models.Argument.id == argument_id).first()
    if not argument:
        raise HTTPException(status_code=404, detail="Argument not found")
        
    # 2. Check if the user has already liked this specific argument
    existing_like = db.query(models.ArgumentLike).filter(
        models.ArgumentLike.argument_id == argument_id, 
        models.ArgumentLike.user_id == current_user.id
    ).first()
    
    if existing_like:
        # toggle: user clicked the heart again, remove the like
        db.delete(existing_like)
        argument.likes_count -= 1
    else:
        # toggle: user liked the argument
        new_like = models.ArgumentLike(argument_id=argument_id, user_id=current_user.id)
        db.add(new_like)
        argument.likes_count += 1
        
    # Save changes
    db.commit()
    db.refresh(argument)

    return argument

@app.post("/upload/", response_model=dict)
def upload_image(file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
    ):
    # Generate a unique filename to avoid collisions
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"uploads/{unique_filename}"

    # Save the uploaded file to the uploads directory
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"image_url": f"http://localhost:8000/uploads/{unique_filename}"}

