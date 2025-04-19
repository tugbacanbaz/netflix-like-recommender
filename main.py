from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

from database import get_db, User, Movie, UserMovieWatch, create_tables
from recommender import MovieRecommender
from models import MovieBase, MovieResponse, MovieRecommendation

app = FastAPI(
    title="Netflix Recommendation System",
    description="An API that provides movie recommendations based on user preferences.",
    version="1.0.0"
)

# Pydantic modelleri
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class MovieCreate(MovieBase):
    pass

class MovieRating(BaseModel):
    movie_id: int
    rating: float = Field(..., ge=0.0, le=5.0)

class ClusterInfo(BaseModel):
    cluster_id: int
    movie_count: int
    average_rating: float
    genres: List[str]

# Öneri sistemi instance'ı
recommender = MovieRecommender(n_clusters=5)

@app.on_event("startup")
async def startup_event():
    create_tables()

# Kullanıcı endpoint'leri
@app.post("/users/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten kullanılıyor")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Bu email adresi zaten kullanılıyor")
    
    db_user = User(username=user.username, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return user

# Film endpoint'leri
@app.post("/movies/", response_model=MovieResponse, status_code=201)
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    db_movie = Movie(**movie.dict())
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

@app.get("/movies/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Film bulunamadı")
    return movie

# Film izleme ve puanlama endpoint'i
@app.post("/users/{user_id}/rate-movie", status_code=201)
def rate_movie(user_id: int, rating: MovieRating, db: Session = Depends(get_db)):
    # Kullanıcı ve film kontrolü
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    movie = db.query(Movie).filter(Movie.id == rating.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Film bulunamadı")
    
    # Puanlama kaydı oluştur veya güncelle
    watch_record = db.query(UserMovieWatch).filter(
        UserMovieWatch.user_id == user_id,
        UserMovieWatch.movie_id == rating.movie_id
    ).first()
    
    if watch_record:
        watch_record.rating = rating.rating
    else:
        watch_record = UserMovieWatch(
            user_id=user_id,
            movie_id=rating.movie_id,
            rating=rating.rating
        )
        db.add(watch_record)
    
    db.commit()
    return {"message": "Film başarıyla puanlandı"}

# Öneri endpoint'leri
@app.get("/recommendations/{user_id}", response_model=List[MovieRecommendation])
async def get_recommendations(user_id: int, n_recommendations: int = 5, db: Session = Depends(get_db)):
    """
    Get movie recommendations for a user
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's ratings
        user_ratings = db.query(UserMovieWatch).filter(UserMovieWatch.user_id == user_id).all()
        print(f"User {user_id} has {len(user_ratings)} ratings")
        
        # Get recommendations
        try:
            recommendations = recommender.get_user_recommendations(user_id, n_recommendations)
            print(f"Got {len(recommendations)} recommendations")
            
            # The recommendations are already MovieRecommendation objects
            return recommendations
            
        except Exception as e:
            print(f"Error getting recommendations: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/movies/{movie_id}/similar", response_model=List[MovieRecommendation])
def get_similar_movies(
    movie_id: int,
    n_similar: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    try:
        similar_movies = recommender.get_similar_movies(movie_id, n_similar)
        return similar_movies
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Öneri sistemi hatası")

# Küme endpoint'leri
@app.get("/clusters/", response_model=List[ClusterInfo])
def get_clusters(db: Session = Depends(get_db)):
    """Tüm kümelerin bilgilerini döndürür"""
    clusters = []
    for cluster_id in range(recommender.n_clusters):
        movies = recommender.get_movies_by_cluster(cluster_id)
        if movies:
            # Küme istatistiklerini hesapla
            genres = set()
            total_rating = 0
            rating_count = 0
            
            for movie in movies:
                genres.update(g.strip() for g in movie.genre.split(','))
                # Film puanlarını topla
                ratings = db.query(UserMovieWatch.rating).filter(
                    UserMovieWatch.movie_id == movie.id
                ).all()
                for rating in ratings:
                    total_rating += rating[0]
                    rating_count += 1
            
            avg_rating = total_rating / rating_count if rating_count > 0 else 0
            
            clusters.append(ClusterInfo(
                cluster_id=cluster_id,
                movie_count=len(movies),
                average_rating=avg_rating,
                genres=list(genres)
            ))
    
    return clusters

@app.get("/clusters/{cluster_id}/movies", response_model=List[MovieResponse])
def get_cluster_movies(
    cluster_id: int,
    db: Session = Depends(get_db)
):
    """Belirli bir kümedeki tüm filmleri döndürür"""
    try:
        movies = recommender.get_movies_by_cluster(cluster_id)
        return movies
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/popular-movies", response_model=List[MovieRecommendation])
def get_popular_movies(
    n_movies: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """En popüler filmleri döndürür"""
    try:
        popular_movies = recommender.get_popular_movies(n_movies)
        return popular_movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Öneri sistemi hatası: {str(e)}")

@app.get("/cluster-recommendations/{user_id}", response_model=List[MovieRecommendation])
async def get_cluster_recommendations(
    user_id: int, 
    n_recommendations: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get movie recommendations for a user using cluster-based collaborative filtering
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get recommendations
        try:
            recommendations = recommender.get_cluster_recommendations(user_id, n_recommendations)
            return recommendations
        except Exception as e:
            print(f"Error getting cluster recommendations: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error getting cluster recommendations: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import logging
    
    # Loglama ayarlarını yapılandır
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("uvicorn")
    
    try:
        # Veritabanı tablolarını oluştur
        logger.info("Veritabanı tabloları oluşturuluyor...")
        create_tables()
        logger.info("Veritabanı tabloları başarıyla oluşturuldu.")
        
        # Öneri sistemini başlat
        logger.info("Öneri sistemi başlatılıyor...")
        recommender = MovieRecommender(n_clusters=5)
        logger.info("Öneri sistemi başarıyla başlatıldı.")
        
        # Uygulamayı başlat
        logger.info("FastAPI uygulaması başlatılıyor...")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except Exception as e:
        logger.error(f"Uygulama başlatılırken hata oluştu: {str(e)}")
        raise
    
#http://localhost:8000/docs
#http://localhost:8000/redoc