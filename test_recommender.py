import unittest
from database import SessionLocal, User, Movie, UserMovieWatch, create_tables
from recommender import MovieRecommender
import numpy as np

class TestMovieRecommender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database and add sample data"""
        # Create tables
        create_tables()
        
        # Create database session
        cls.db = SessionLocal()
        
        # Create sample users
        cls.users = []
        for i in range(1, 6):
            user = User(username=f"test_user_{i}", email=f"test_user_{i}@example.com")
            cls.db.add(user)
            cls.users.append(user)
        cls.db.commit()
        
        # Create sample movies
        cls.movies = []
        genres = ["Action", "Drama", "Comedy", "Sci-Fi", "Horror"]
        for i in range(1, 11):
            movie = Movie(
                title=f"Test Movie {i}",
                genre=genres[i % len(genres)],
                release_year=2000 + i,
                duration=120 + i * 10,
                description=f"Test description for movie {i}"
            )
            cls.db.add(movie)
            cls.movies.append(movie)
        cls.db.commit()
        
        # Create sample ratings
        for user in cls.users:
            for movie in cls.movies[:5]:  # Each user rates first 5 movies
                rating = UserMovieWatch(
                    user_id=user.id,
                    movie_id=movie.id,
                    rating=np.random.uniform(1, 5)
                )
                cls.db.add(rating)
        cls.db.commit()
        
        # Initialize recommender
        cls.recommender = MovieRecommender(n_clusters=3)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        cls.db.close()
    
    def test_user_recommendations(self):
        """Test user-based recommendations"""
        user_id = self.users[0].id
        recommendations = self.recommender.get_user_recommendations(user_id, n_recommendations=3)
        
        self.assertIsInstance(recommendations, list)
        self.assertLessEqual(len(recommendations), 3)
        for movie, rating in recommendations:
            self.assertIsInstance(movie, Movie)
            self.assertIsInstance(rating, float)
            self.assertGreaterEqual(rating, 0)
            self.assertLessEqual(rating, 5)
    
    def test_cluster_recommendations(self):
        """Test cluster-based recommendations"""
        user_id = self.users[0].id
        recommendations = self.recommender.get_cluster_recommendations(user_id, n_recommendations=3)
        
        self.assertIsInstance(recommendations, list)
        self.assertLessEqual(len(recommendations), 3)
        for movie, rating in recommendations:
            self.assertIsInstance(movie, Movie)
            self.assertIsInstance(rating, float)
            self.assertGreaterEqual(rating, 0)
            self.assertLessEqual(rating, 5)
    
    def test_similar_movies(self):
        """Test similar movies recommendations"""
        movie_id = self.movies[0].id
        similar_movies = self.recommender.get_similar_movies(movie_id, n_similar=3)
        
        self.assertIsInstance(similar_movies, list)
        self.assertLessEqual(len(similar_movies), 3)
        for movie, similarity in similar_movies:
            self.assertIsInstance(movie, Movie)
            self.assertIsInstance(similarity, float)
            self.assertGreaterEqual(similarity, 0)
            self.assertLessEqual(similarity, 1)
    
    def test_movies_by_cluster(self):
        """Test getting movies by cluster"""
        for cluster_id in range(self.recommender.n_clusters):
            movies = self.recommender.get_movies_by_cluster(cluster_id)
            self.assertIsInstance(movies, list)
            for movie in movies:
                self.assertIsInstance(movie, Movie)
    
    def test_invalid_user_id(self):
        """Test handling of invalid user ID"""
        with self.assertRaises(ValueError):
            self.recommender.get_user_recommendations(999)
    
    def test_invalid_movie_id(self):
        """Test handling of invalid movie ID"""
        with self.assertRaises(ValueError):
            self.recommender.get_similar_movies(999)
    
    def test_invalid_cluster_id(self):
        """Test handling of invalid cluster ID"""
        with self.assertRaises(ValueError):
            self.recommender.get_movies_by_cluster(999)

if __name__ == '__main__':
    unittest.main() 