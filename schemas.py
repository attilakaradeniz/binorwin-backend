from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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

    # This tells Pydantic to read the data even if it's not a regular dictionary (SQLAlchemy model)
    class Config:
        orm_mode = True

# ARGUMENT SCHEMAS 

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

    class Config:
        orm_mode = True