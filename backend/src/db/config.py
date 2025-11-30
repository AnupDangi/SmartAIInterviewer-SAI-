"""
Database configuration for Neon Postgres
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Neon Postgres connection string
# Format: postgresql://user:password@host/database?sslmode=require
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/dbname?sslmode=require"
)



# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables, cleanup old RAG tables, and run migrations
    """
    # Drop old RAG tables if they exist
    try:
        with engine.connect() as conn:
            # Drop old RAG tables
            conn.execute(text("DROP TABLE IF EXISTS chunks CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS files CASCADE"))
            # Drop other unused tables
            conn.execute(text("DROP TABLE IF EXISTS messages CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS sessions CASCADE"))
            conn.commit()
    except Exception as e:
        print(f"Note: Could not drop old tables (they may not exist): {e}")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
    
    # Run migrations
    try:
        with engine.connect() as conn:
            # Migration: Add session_run_id column to interview_sessions
            # Check if column exists first
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='interview_sessions' AND column_name='session_run_id'
            """))
            
            if result.fetchone() is None:
                print("Running migration: Adding session_run_id column...")
                conn.execute(text("""
                    ALTER TABLE interview_sessions 
                    ADD COLUMN session_run_id UUID
                """))
                
                # Create index
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_interview_sessions_run_id 
                    ON interview_sessions(session_run_id)
                """))
                
                # Update existing rows to have a unique session_run_id (backward compatibility)
                conn.execute(text("""
                    UPDATE interview_sessions 
                    SET session_run_id = id 
                    WHERE session_run_id IS NULL
                """))
                
                conn.commit()
                print("Migration completed: session_run_id column added")
            else:
                print("Migration skipped: session_run_id column already exists")
    except Exception as e:
        print(f"Warning: Migration failed (column may already exist): {e}")
        # Don't fail if migration fails - column might already exist

