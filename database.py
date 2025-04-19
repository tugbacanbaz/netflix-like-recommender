from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/netflix_recommender")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model
Base = declarative_base()

# User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    watched_movies = relationship(
        "Movie",
        secondary="user_movie_watches",
        back_populates="watched_by"
    )
    watch_history = relationship(
        "UserMovieWatch",
        back_populates="user",
        viewonly=True
    )

# Movie model
class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    genre = Column(String)
    release_year = Column(Integer)
    duration = Column(Integer)  # in minutes
    description = Column(String)
    
    # Relationships
    watched_by = relationship(
        "User",
        secondary="user_movie_watches",
        back_populates="watched_movies"
    )
    watch_history = relationship(
        "UserMovieWatch",
        back_populates="movie",
        viewonly=True
    )

# User-Movie watch history model
class UserMovieWatch(Base):
    __tablename__ = "user_movie_watches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    movie_id = Column(Integer, ForeignKey('movies.id'))
    rating = Column(Float)
    watched_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship(
        "User",
        back_populates="watch_history"
    )
    movie = relationship(
        "Movie",
        back_populates="watch_history"
    )

# Database connection dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create database tables
def create_tables():
    Base.metadata.create_all(bind=engine) 