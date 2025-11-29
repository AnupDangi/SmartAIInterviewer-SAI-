#!/usr/bin/env python3
"""
Run database migration to add session_run_id column
"""
from src.db.config import engine
from sqlalchemy import text

def run_migration():
    """Add session_run_id column to interview_sessions table"""
    try:
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='interview_sessions' AND column_name='session_run_id'
            """))
            
            if result.fetchone() is None:
                print("Adding session_run_id column...")
                conn.execute(text("""
                    ALTER TABLE interview_sessions 
                    ADD COLUMN session_run_id UUID
                """))
                
                print("Creating index...")
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_interview_sessions_run_id 
                    ON interview_sessions(session_run_id)
                """))
                
                print("Updating existing rows...")
                conn.execute(text("""
                    UPDATE interview_sessions 
                    SET session_run_id = id 
                    WHERE session_run_id IS NULL
                """))
                
                conn.commit()
                print("✅ Migration completed successfully!")
            else:
                print("✅ Column already exists, migration not needed")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()

