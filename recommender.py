from database import SessionLocal, User, Movie, UserMovieWatch
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import List, Tuple
import json
from models import MovieRecommendation  # MovieRecommendation sınıfını models.py dosyasından import et

class MovieRecommender:
    def __init__(self, n_clusters=5):
        self.db = SessionLocal()
        self.user_movie_matrix = None
        self.user_similarity_matrix = None
        self.movie_features = None
        self.kmeans = None
        self.n_clusters = n_clusters
        self._build_user_movie_matrix()
        self._build_movie_features()
        self._fit_kmeans()
    
    def _build_user_movie_matrix(self):
        """Build user-movie rating matrix"""
        # Get all ratings
        ratings = self.db.query(UserMovieWatch).all()
        
        # Create a dictionary to store user-movie ratings
        ratings_dict = {}
        for rating in ratings:
            if rating.user_id not in ratings_dict:
                ratings_dict[rating.user_id] = {}
            ratings_dict[rating.user_id][rating.movie_id] = rating.rating
        
        # Convert to DataFrame
        self.user_movie_matrix = pd.DataFrame(ratings_dict).T
        
        # Fill NaN values with 0
        self.user_movie_matrix = self.user_movie_matrix.fillna(0)
        
        # Calculate user similarity matrix
        self.user_similarity_matrix = cosine_similarity(self.user_movie_matrix)
    
    def _build_movie_features(self):
        """Build movie features matrix for clustering"""
        movies = self.db.query(Movie).all()
        
        # Create features dictionary
        features_dict = {}
        for movie in movies:
            # Convert genre string to one-hot encoding
            genres = [g.strip() for g in movie.genre.split(',')]
            genre_dict = {genre: 1 for genre in genres}
            
            # Combine all features
            features = {
                'duration': movie.duration,
                'release_year': movie.release_year,
                **genre_dict
            }
            features_dict[movie.id] = features
        
        # Convert to DataFrame
        self.movie_features = pd.DataFrame(features_dict).T
        
        # Fill NaN values with 0 (for genres that don't exist for some movies)
        self.movie_features = self.movie_features.fillna(0)
        
        # Scale the features
        scaler = StandardScaler()
        self.movie_features_scaled = pd.DataFrame(
            scaler.fit_transform(self.movie_features),
            columns=self.movie_features.columns,
            index=self.movie_features.index
        )
    
    def _fit_kmeans(self):
        """Fit KMeans clustering on movie features"""
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
        self.movie_clusters = self.kmeans.fit_predict(self.movie_features_scaled)
        
        # Add cluster labels to movie features
        self.movie_features['cluster'] = self.movie_clusters
    
    def get_movies_by_cluster(self, cluster_id: int) -> List[Movie]:
        """
        Get all movies in a specific cluster
        
        Args:
            cluster_id: ID of the cluster to get movies from
            
        Returns:
            List of Movie objects in the cluster
        """
        if cluster_id >= self.n_clusters:
            raise ValueError(f"Cluster {cluster_id} does not exist")
        
        # Get movie IDs in the cluster
        cluster_movie_ids = self.movie_features[self.movie_features['cluster'] == cluster_id].index
        
        # Get Movie objects
        movies = self.db.query(Movie).filter(Movie.id.in_(cluster_movie_ids)).all()
        return movies
    
    def get_cluster_recommendations(self, user_id: int, n_recommendations: int = 5) -> List[MovieRecommendation]:
        """
        Get movie recommendations for a user using cluster-based collaborative filtering
        
        Args:
            user_id: ID of the user to get recommendations for
            n_recommendations: Number of recommendations to return
            
        Returns:
            List of MovieRecommendation objects
        """
        if user_id not in self.user_movie_matrix.index:
            raise ValueError(f"User {user_id} not found in the database")
        
        # Get user's rated movies
        user_ratings = self.user_movie_matrix.loc[user_id]
        unrated_movies = user_ratings[user_ratings == 0].index
        
        # Get user's favorite cluster
        rated_movies = user_ratings[user_ratings > 0].index
        if len(rated_movies) > 0:
            favorite_cluster = self.movie_features.loc[rated_movies, 'cluster'].mode()[0]
        else:
            # If user hasn't rated any movies, use random cluster
            favorite_cluster = np.random.randint(0, self.n_clusters)
        
        # Get movies from favorite cluster that user hasn't rated
        cluster_movies = self.movie_features[
            (self.movie_features['cluster'] == favorite_cluster) & 
            (self.movie_features.index.isin(unrated_movies))
        ].index
        
        if len(cluster_movies) == 0:
            # If no movies in favorite cluster, get from all unrated movies
            cluster_movies = unrated_movies
        
        # Calculate predicted ratings for cluster movies
        predictions = []
        for movie_id in cluster_movies:
            # Get ratings for this movie from similar users
            movie_ratings = self.user_movie_matrix[movie_id]
            
            # Calculate weighted average of ratings
            weighted_ratings = movie_ratings * self.user_similarity_matrix[self.user_movie_matrix.index.get_loc(user_id)]
            predicted_rating = weighted_ratings.sum() / (self.user_similarity_matrix[self.user_movie_matrix.index.get_loc(user_id)].sum() + 1e-8)
            
            predictions.append((movie_id, predicted_rating))
        
        # Sort predictions by rating
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        # Get top N recommendations
        top_recommendations = []
        for movie_id, predicted_rating in predictions[:n_recommendations]:
            movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
            if movie:
                top_recommendations.append(MovieRecommendation(
                    id=movie.id,
                    title=movie.title,
                    genre=movie.genre,
                    release_year=movie.release_year,
                    duration=movie.duration,
                    description=movie.description,
                    predicted_rating=predicted_rating,
                    cluster_id=favorite_cluster
                ))
        
        return top_recommendations
    
    def get_user_recommendations(self, user_id: int, n_recommendations: int = 5) -> List[MovieRecommendation]:
        """
        Get movie recommendations for a user using collaborative filtering
        
        Args:
            user_id: ID of the user to get recommendations for
            n_recommendations: Number of recommendations to return
            
        Returns:
            List of MovieRecommendation objects
        """
        if user_id not in self.user_movie_matrix.index:
            raise ValueError(f"User {user_id} not found in the database")
        
        # Get user's rated movies
        user_ratings = self.user_movie_matrix.loc[user_id]
        unrated_movies = user_ratings[user_ratings == 0].index
        
        # Get similar users
        user_idx = self.user_movie_matrix.index.get_loc(user_id)
        similar_users = self.user_similarity_matrix[user_idx]
        
        # Calculate predicted ratings for unrated movies
        predictions = []
        for movie_id in unrated_movies:
            # Get ratings for this movie from similar users
            movie_ratings = self.user_movie_matrix[movie_id]
            
            # Calculate weighted average of ratings
            weighted_ratings = movie_ratings * similar_users
            predicted_rating = weighted_ratings.sum() / (similar_users.sum() + 1e-8)
            
            predictions.append((movie_id, predicted_rating))
        
        # Sort predictions by rating
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        # Get top N recommendations
        top_recommendations = []
        for movie_id, predicted_rating in predictions[:n_recommendations]:
            movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
            if movie:
                top_recommendations.append(MovieRecommendation(
                    id=movie.id,
                    title=movie.title,
                    genre=movie.genre,
                    release_year=movie.release_year,
                    duration=movie.duration,
                    description=movie.description,
                    predicted_rating=predicted_rating
                ))
        
        return top_recommendations
    
    def get_similar_movies(self, movie_id: int, n_similar: int = 5) -> List[MovieRecommendation]:
        """
        Get similar movies based on user ratings
        
        Args:
            movie_id: ID of the movie to find similar movies for
            n_similar: Number of similar movies to return
            
        Returns:
            List of MovieRecommendation objects
        """
        if movie_id not in self.user_movie_matrix.columns:
            raise ValueError(f"Movie {movie_id} not found in the database")
        
        # Calculate movie similarity using item-based collaborative filtering
        movie_similarity = cosine_similarity(self.user_movie_matrix.T)
        movie_idx = self.user_movie_matrix.columns.get_loc(movie_id)
        
        # Get similar movies
        similar_movies = []
        for idx, similarity in enumerate(movie_similarity[movie_idx]):
            if idx != movie_idx:  # Skip the movie itself
                similar_movie_id = int(self.user_movie_matrix.columns[idx])  # Convert numpy.int64 to int
                movie = self.db.query(Movie).filter(Movie.id == similar_movie_id).first()
                if movie:
                    similar_movies.append((movie, float(similarity)))  # Convert numpy.float64 to float
        
        # Sort by similarity and return top N
        similar_movies.sort(key=lambda x: x[1], reverse=True)
        
        # Convert to MovieRecommendation objects
        movie_recommendations = []
        for movie, similarity_score in similar_movies[:n_similar]:
            movie_recommendations.append(MovieRecommendation(
                id=movie.id,
                title=movie.title,
                genre=movie.genre,
                release_year=movie.release_year,
                duration=movie.duration,
                description=movie.description,
                similarity_score=similarity_score
            ))
        
        return movie_recommendations
    
    def get_popular_movies(self, n_movies: int = 5) -> List[MovieRecommendation]:
        """
        Get most popular movies based on average ratings
        
        Args:
            n_movies: Number of popular movies to return
            
        Returns:
            List of MovieRecommendation objects
        """
        # Calculate average ratings for each movie
        movie_ratings = self.user_movie_matrix.mean()
        
        # Get top N movies
        top_movies = []
        for movie_id, avg_rating in movie_ratings.nlargest(n_movies).items():
            movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
            if movie:
                top_movies.append((movie, avg_rating))
        
        # Convert to MovieRecommendation objects
        movie_recommendations = []
        for movie, avg_rating in top_movies:
            movie_recommendations.append(MovieRecommendation(
                id=movie.id,
                title=movie.title,
                genre=movie.genre,
                release_year=movie.release_year,
                duration=movie.duration,
                description=movie.description,
                predicted_rating=avg_rating
            ))
        
        return movie_recommendations
    
    def close(self):
        """Close database connection"""
        self.db.close()

# Example usage
if __name__ == "__main__":
    recommender = MovieRecommender()
    try:
        # Get recommendations for user 1
        print("\nTop 5 recommendations for user 1:")
        recommendations = recommender.get_user_recommendations(1)
        for movie, rating in recommendations:
            print(f"{movie.title} (Predicted rating: {rating:.1f})")
        
        # Get similar movies for movie 1
        print("\nMovies similar to The Shawshank Redemption:")
        similar_movies = recommender.get_similar_movies(1)
        for movie in similar_movies:
            print(f"{movie.title} (Similarity: {movie.similarity_score:.2f})")
        
        # Get popular movies
        print("\nMost popular movies:")
        popular_movies = recommender.get_popular_movies()
        for movie in popular_movies:
            print(f"{movie.title} (Predicted rating: {movie.predicted_rating:.1f})")
            
    finally:
        recommender.close() 