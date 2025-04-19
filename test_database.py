from database import create_tables, SessionLocal, User, Movie, UserMovieWatch
from datetime import datetime

def test_database_connection():
    try:
        # Create tables
        create_tables()
        print("✅ Tables created successfully!")
        
        # Get database connection
        db = SessionLocal()
        print("✅ Database connection successful!")
        
        # Run a simple query
        user_count = db.query(User).count()
        print(f"✅ Found {user_count} users in the database.")
        
        # Close connection
        db.close()
        print("✅ Database connection closed successfully.")
        
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing database connection...")
    success = test_database_connection()
    
    if success:
        print("\n🎉 Database connection and tables are working successfully!")
    else:
        print("\n❌ There is a problem with the database connection or tables.") 