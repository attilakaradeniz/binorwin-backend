from sqlalchemy import Column, Integer, String, ForeignKey, DateTime # DateTime eklendi
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # func eklendi (otomatik saat için)
from database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    image_url = Column(String)
    bin_votes = Column(Integer, default=0)
    win_votes = Column(Integer, default=0)
    
    # Yeni eklenen satır: Sunucunun o anki saatini otomatik kaydeder
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    arguments = relationship("Argument", back_populates="post", cascade="all, delete-orphan")

class Argument(Base):
    __tablename__ = "arguments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    action_type = Column(String) 
    content = Column(String)
    
    # Yeni eklenen satır: Yorumun yapıldığı saat
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="arguments")