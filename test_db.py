import sys
from database import engine, create_tables, DATABASE_URL
from sqlalchemy import text
import traceback

def test_connection():
    print(f"Attempting to connect to database with URL: {DATABASE_URL}")
    try:
        # Try to connect to the database
        print("Establishing connection...")
        with engine.connect() as connection:
            print("Connection established, executing test query...")
            result = connection.execute(text("SELECT 1"))
            print("✅ Successfully connected to the database!")
            
            # Try to create tables
            print("Creating database tables...")
            create_tables()
            print("✅ Successfully created database tables!")
            
    except Exception as e:
        print(f"❌ Error connecting to the database:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("Testing database connection...")
    test_connection() 