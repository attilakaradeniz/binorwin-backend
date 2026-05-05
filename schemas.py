from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# user & token schemas

class UserCreate(BaseModel):
    username: str
    email: str 
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# post schemas

# Schema for creating a new Post (what we expect from the Android app)
class PostCreate(BaseModel):
    title: str
    image_url: str

# Schema for returning a Post back to the user (what we send out)
class PostResponse(BaseModel):
    id: int
    title: str
    image_url: str
    bin_votes: int
    win_votes: int
    created_at: datetime
    
    # NEW: Link the post to the user
    # temporaryly user id & response OPTIONAL (later will be removed)
    # owner_id: int 
    # owner: UserResponse 
    owner_id: Optional[int] = None
    owner: Optional[UserResponse] = None    

    # This tells Pydantic to read the data even if it's not a regular dictionary (SQLAlchemy model)
    class Config:
        orm_mode = True


# argument schemas

# Base schema for arguments
class ArgumentBase(BaseModel):
    action_type: str  # This should strictly be "bin" or "win"
    content: str      # The actual comment text

# Schema for creating a new argument
class ArgumentCreate(ArgumentBase):
    pass

# Schema for returning an argument to the user
class ArgumentResponse(ArgumentBase):
    id: int
    post_id: int
    created_at: datetime
    
    # NEW: Link the argument to the user
    # owner_id: int 
    # owner: UserResponse 
    # temporaryly user id & response OPTIONAL (later will be removed)
    owner_id: Optional[int] = None
    owner: Optional[UserResponse] = None    

    class Config:
        orm_mode = True