from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# Model for the main post (the item to be voted on)
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    image_url = Column(String)
    bin_votes = Column(Integer, default=0)
    win_votes = Column(Integer, default=0)

    # Relationship to fetch arguments easily
    arguments = relationship("Argument", back_populates="post")


# Model for the arguments (Why bin it? / How win it?)
class Argument(Base):
    __tablename__ = "arguments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    action_type = Column(String) # Will store "bin" or "win"
    content = Column(String)

    # Relationship back to the post
    post = relationship("Post", back_populates="arguments")