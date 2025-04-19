from database import SessionLocal, User, Movie, UserMovieWatch, Base, engine
from datetime import datetime
import random

def clear_database():
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    # Recreate all tables
    Base.metadata.create_all(bind=engine)

def seed_database():
    db = SessionLocal()
    try:
        # Clear existing data
        print("Clearing existing data...")
        clear_database()
        print("✅ Database cleared successfully!")

        # Create sample users (20 users)
        users = []
        for i in range(1, 21):
            users.append(User(
                username=f"user_{i}",
                email=f"user_{i}@example.com"
            ))
        
        # Add users to database
        for user in users:
            db.add(user)
        db.commit()
        
        # Create sample movies (50 movies)
        movies = [
            # Drama movies
            Movie(title="The Shawshank Redemption", genre="Drama", release_year=1994, duration=142, description="Two imprisoned men bond over a number of years..."),
            Movie(title="The Godfather", genre="Drama, Crime", release_year=1972, duration=175, description="The aging patriarch of an organized crime dynasty..."),
            Movie(title="Forrest Gump", genre="Drama", release_year=1994, duration=142, description="The life journey of a man with low intelligence..."),
            Movie(title="The Green Mile", genre="Drama", release_year=1999, duration=189, description="The lives of guards and inmates on death row..."),
            Movie(title="Schindler's List", genre="Drama, History", release_year=1993, duration=195, description="A businessman saves the lives of over a thousand Jewish refugees..."),
            
            # Action movies
            Movie(title="The Dark Knight", genre="Action, Crime, Drama", release_year=2008, duration=152, description="When the menace known as the Joker wreaks havoc..."),
            Movie(title="Inception", genre="Action, Sci-Fi", release_year=2010, duration=148, description="A thief who steals corporate secrets through dream-sharing technology..."),
            Movie(title="The Matrix", genre="Action, Sci-Fi", release_year=1999, duration=136, description="A computer programmer discovers a mysterious world..."),
            Movie(title="Mad Max: Fury Road", genre="Action, Adventure", release_year=2015, duration=120, description="A woman rebels against a tyrannical ruler..."),
            Movie(title="John Wick", genre="Action, Crime", release_year=2014, duration=101, description="An ex-hitman comes out of retirement to track down the gangsters..."),
            
            # Comedy movies
            Movie(title="The Hangover", genre="Comedy", release_year=2009, duration=100, description="Three friends wake up from a bachelor party..."),
            Movie(title="Superbad", genre="Comedy", release_year=2007, duration=113, description="Two high school friends try to buy alcohol for a party..."),
            Movie(title="Bridesmaids", genre="Comedy", release_year=2011, duration=125, description="A woman competes with another bridesmaid for the position of maid of honor..."),
            Movie(title="The 40-Year-Old Virgin", genre="Comedy", release_year=2005, duration=116, description="A man's friends try to help him lose his virginity..."),
            Movie(title="Deadpool", genre="Comedy, Action", release_year=2016, duration=108, description="A former Special Forces operative turned mercenary..."),
            
            # Sci-Fi movies
            Movie(title="Interstellar", genre="Sci-Fi, Adventure", release_year=2014, duration=169, description="A team of explorers travel through a wormhole in space..."),
            Movie(title="Blade Runner 2049", genre="Sci-Fi, Action", release_year=2017, duration=164, description="A blade runner discovers a long-buried secret..."),
            Movie(title="The Martian", genre="Sci-Fi, Adventure", release_year=2015, duration=144, description="An astronaut is left behind on Mars..."),
            Movie(title="Arrival", genre="Sci-Fi, Drama", release_year=2016, duration=116, description="A linguist works with the military to communicate with alien lifeforms..."),
            Movie(title="Ex Machina", genre="Sci-Fi, Drama", release_year=2014, duration=108, description="A programmer is selected to participate in a breakthrough experiment..."),
            
            # Horror movies
            Movie(title="The Shining", genre="Horror", release_year=1980, duration=146, description="A family heads to an isolated hotel for the winter..."),
            Movie(title="A Quiet Place", genre="Horror, Drama", release_year=2018, duration=90, description="A family must live in silence to avoid mysterious creatures..."),
            Movie(title="Get Out", genre="Horror, Mystery", release_year=2017, duration=104, description="A young African-American visits his white girlfriend's parents..."),
            Movie(title="Hereditary", genre="Horror, Mystery", release_year=2018, duration=127, description="A family is haunted by mysterious occurrences..."),
            Movie(title="The Conjuring", genre="Horror, Mystery", release_year=2013, duration=112, description="Paranormal investigators help a family terrorized by a dark presence..."),
            
            # Romance movies
            Movie(title="The Notebook", genre="Romance, Drama", release_year=2004, duration=123, description="A poor yet passionate young man falls in love with a rich young woman..."),
            Movie(title="La La Land", genre="Romance, Musical", release_year=2016, duration=128, description="A jazz pianist falls for an aspiring actress in Los Angeles..."),
            Movie(title="500 Days of Summer", genre="Romance, Comedy", release_year=2009, duration=95, description="A man reflects on his relationship with a woman..."),
            Movie(title="Before Sunrise", genre="Romance, Drama", release_year=1995, duration=101, description="A young man and woman meet on a train in Europe..."),
            Movie(title="Eternal Sunshine of the Spotless Mind", genre="Romance, Sci-Fi", release_year=2004, duration=108, description="A couple undergoes a procedure to erase each other from their memories..."),
            
            # Thriller movies
            Movie(title="Se7en", genre="Thriller, Crime", release_year=1995, duration=127, description="Two detectives track a serial killer..."),
            Movie(title="Gone Girl", genre="Thriller, Drama", release_year=2014, duration=149, description="A man becomes the prime suspect in his wife's disappearance..."),
            Movie(title="The Silence of the Lambs", genre="Thriller, Crime", release_year=1991, duration=118, description="A young FBI cadet must receive the help of an incarcerated cannibalistic serial killer..."),
            Movie(title="Shutter Island", genre="Thriller, Mystery", release_year=2010, duration=138, description="A U.S. Marshal investigates the disappearance of a patient..."),
            Movie(title="Prisoners", genre="Thriller, Drama", release_year=2013, duration=153, description="A father takes matters into his own hands after his daughter goes missing..."),
            
            # Animation movies
            Movie(title="Spirited Away", genre="Animation, Adventure", release_year=2001, duration=125, description="A young girl wanders into a world ruled by gods, witches, and spirits..."),
            Movie(title="The Lion King", genre="Animation, Adventure", release_year=1994, duration=88, description="Lion prince Simba and his father are targeted by his bitter uncle..."),
            Movie(title="Up", genre="Animation, Adventure", release_year=2009, duration=96, description="An elderly widower sets out to fulfill his lifelong dream..."),
            Movie(title="Spider-Man: Into the Spider-Verse", genre="Animation, Action", release_year=2018, duration=117, description="A teenager becomes the Spider-Man of his reality..."),
            Movie(title="Coco", genre="Animation, Adventure", release_year=2017, duration=105, description="A young boy is transported to the Land of the Dead..."),
            
            # Documentary movies
            Movie(title="Planet Earth", genre="Documentary", release_year=2006, duration=550, description="A documentary series about the diversity of habitats around the world..."),
            Movie(title="March of the Penguins", genre="Documentary", release_year=2005, duration=80, description="A documentary about the annual journey of emperor penguins..."),
            Movie(title="Blackfish", genre="Documentary", release_year=2013, duration=83, description="A documentary following the controversial captivity of killer whales..."),
            Movie(title="Jiro Dreams of Sushi", genre="Documentary", release_year=2011, duration=81, description="A documentary about Jiro Ono, an 85-year-old sushi master..."),
            Movie(title="Free Solo", genre="Documentary", release_year=2018, duration=100, description="A documentary about Alex Honnold's free solo climb of El Capitan...")
        ]
        
        # Add movies to database
        for movie in movies:
            db.add(movie)
        db.commit()
        
        print("✅ Sample users and movies added successfully!")
        
        # Get all movie IDs from database
        movie_ids = [movie.id for movie in db.query(Movie).all()]
        
        # Create sample watch history (random ratings for each user-movie pair)
        watch_history = []
        for user in db.query(User).all():
            # Each user watches 10-20 random movies
            num_watches = random.randint(10, 20)
            watched_movies = random.sample(movie_ids, num_watches)
            
            for movie_id in watched_movies:
                # Random rating between 1.0 and 5.0
                rating = round(random.uniform(1.0, 5.0), 1)
                watch_history.append(UserMovieWatch(
                    user_id=user.id,
                    movie_id=movie_id,
                    rating=rating
                ))
        
        for watch in watch_history:
            db.add(watch)
        
        db.commit()
        print("✅ Sample watch history added successfully!")
        
        # Print summary
        user_count = db.query(User).count()
        movie_count = db.query(Movie).count()
        watch_count = db.query(UserMovieWatch).count()
        
        print(f"\nDatabase Summary:")
        print(f"Total Users: {user_count}")
        print(f"Total Movies: {movie_count}")
        print(f"Total Watch Records: {watch_count}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Adding sample data to the database...")
    seed_database() 