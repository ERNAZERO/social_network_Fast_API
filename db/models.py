from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    full_name = Column(String)

    posts = relationship("Post", back_populates="author")
    liked_posts = relationship("Post", secondary="post_like")
    saved_posts = relationship("Post", secondary="post_save")


post_like = Table(
    "post_like",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("post_id", Integer, ForeignKey("posts.id")),
)

post_save = Table(
    "post_save",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("post_id", Integer, ForeignKey("posts.id")),
)


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))

    author = relationship("User", back_populates="posts")
    liked_by = relationship("User", secondary=post_like, back_populates="liked_posts")
    saved_by = relationship("User", secondary=post_save, back_populates="saved_posts")
