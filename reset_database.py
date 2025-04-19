from database import engine, Base
from sqlalchemy import text

def reset_database():
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped successfully!")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("Resetting database...")
    reset_database() 