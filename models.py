from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships to connect user with their posts and arguments
    posts = relationship("Post", back_populates="owner")
    arguments = relationship("Argument", back_populates="owner")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    image_url = Column(String)
    bin_votes = Column(Integer, default=0)
    win_votes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign key linking the post to the user who created it
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    owner = relationship("User", back_populates="posts")
    arguments = relationship("Argument", back_populates="post", cascade="all, delete-orphan")

class Argument(Base):
    __tablename__ = "arguments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    action_type = Column(String) 
    content = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign key linking the argument to the user who created it
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    post = relationship("Post", back_populates="arguments")
    owner = relationship("User", back_populates="arguments")