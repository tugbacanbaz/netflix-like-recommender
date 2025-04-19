# Netflix-like Movie Recommendation System

This project is an API that provides personalized movie recommendations based on user viewing preferences. The system generates recommendations using both collaborative filtering and K-means clustering algorithms.

## Features

- User-based movie recommendations
- Cluster-based movie recommendations
- Similar movie recommendations
- Popular movie recommendations
- Movie rating system
- K-means clustering for movie grouping
- RESTful API endpoints
- PostgreSQL database
- SQLAlchemy ORM
- FastAPI web framework

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Create PostgreSQL database:
```sql
CREATE DATABASE netflix_recommender;
```

3. Create `.env` file:
```
DATABASE_URL=postgresql://username:password@localhost:5432/netflix_recommender
```

4. Create database tables:
```bash
python -c "from database import create_tables; create_tables()"
```

5. Load sample data:
```bash
python seed_database.py
```

## API Endpoints

### User Operations

- `POST /users/`: Create a new user
- `GET /users/{user_id}`: Get user information

### Movie Operations

- `POST /movies/`: Add a new movie
- `GET /movies/{movie_id}`: Get movie information
- `POST /users/{user_id}/rate-movie`: Rate a movie

### Recommendation Operations

- `GET /recommendations/{user_id}`: Get movie recommendations for a user
  - Query parameters:
    - `n_recommendations`: Number of recommendations (default: 5)

- `GET /similar-movies/{movie_id}`: Get similar movies
  - Query parameters:
    - `n_similar`: Number of similar movies (default: 5)

- `GET /popular-movies`: Get popular movies
  - Query parameters:
    - `n_movies`: Number of popular movies (default: 5)

- `GET /cluster-recommendations/{user_id}`: Get cluster-based movie recommendations
  - Query parameters:
    - `n_recommendations`: Number of recommendations (default: 5)

## Example Usage

### Creating a User
```bash
curl -X POST "http://localhost:8000/users/" \
     -H "Content-Type: application/json" \
     -d '{"username": "test_user", "email": "test@example.com", "password": "password123"}'
```

### Rating a Movie
```bash
curl -X POST "http://localhost:8000/users/1/rate-movie" \
     -H "Content-Type: application/json" \
     -d '{"movie_id": 1, "rating": 4.5}'
```

### Getting Movie Recommendations
```bash
curl "http://localhost:8000/recommendations/1?n_recommendations=5"
```

### Getting Similar Movies
```bash
curl "http://localhost:8000/similar-movies/1?n_similar=5"
```

### Getting Popular Movies
```bash
curl "http://localhost:8000/popular-movies?n_movies=5"
```

### Getting Cluster-based Recommendations
```bash
curl "http://localhost:8000/cluster-recommendations/1?n_recommendations=5"
```

## Testing

To run the tests:
```bash
python -m pytest test_recommender.py
```

## Known Issues and Warnings

### SQLAlchemy Relationship Warnings

When running the application, you may see SQLAlchemy warnings about relationship conflicts. These warnings are related to the relationship definitions in the database models. The application still works correctly despite these warnings.

To fix these warnings, you can update the relationship definitions in `database.py` as follows:

```python
# In User model
watch_history = relationship(
    "UserMovieWatch",
    back_populates="user",
    viewonly=True
)

# In Movie model
watch_history = relationship(
    "UserMovieWatch",
    back_populates="movie",
    viewonly=True
)
```

### Pydantic Warning

You may see a warning about `orm_mode` being renamed to `from_attributes` in Pydantic V2. This is a minor issue and doesn't affect functionality. To fix this warning, update your Pydantic models to use `from_attributes=True` instead of `orm_mode=True`.

### FastAPI Deprecation Warning

The application uses `@app.on_event("startup")` which is deprecated in newer versions of FastAPI. To fix this warning, you can update the code to use the new lifespan event handlers:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Veritabanı tabloları oluşturuluyor...")
    create_tables()
    print("Veritabanı tabloları başarıyla oluşturuldu.")
    
    print("Öneri sistemi başlatılıyor...")
    app.state.recommender = MovieRecommender()
    print("Öneri sistemi başarıyla başlatıldı.")
    
    print("FastAPI uygulaması başlatılıyor...")
    yield
    
    # Shutdown
    print("FastAPI uygulaması kapatılıyor...")
    app.state.recommender.close()
    print("FastAPI uygulaması başarıyla kapatıldı.")

app = FastAPI(lifespan=lifespan)
```

### Port Already in Use

If you see an error like `[Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000): [winerror 10048] normal olarak her yuva adresi (iletişim kuralı/ağ adresi/bağlantı noktası) için yalnızca bir kullanıma izin veriliyor`, it means that port 8000 is already in use. This can happen if you have another instance of the application running or if another application is using the same port.

To fix this, you can:
1. Stop the other application using port 8000
2. Change the port in the `main.py` file:
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
```
