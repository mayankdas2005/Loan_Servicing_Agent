import os
import psycopg2
from dotenv import load_dotenv

# --- Add this function to setup_postgres_db.py ---

def create_applications_table():
    """
    Creates the 'applications' table to log all finalized loans.
    """
    
    # 1. Load credentials (copy from your setup_database function)
    load_dotenv("api_secret.env") 
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_NAME = os.environ.get("DB_NAME", "postgres")

    if not DB_PASSWORD:
        print("Error: DB_PASSWORD not found.")
        return

    # 2. Define the table structure
    # This table will store the final, approved loan details
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS applications2 (
        application_id TEXT PRIMARY KEY,
        customer_id INTEGER REFERENCES customers(id),
        plan_name TEXT NOT NULL,
        amount INTEGER NOT NULL,
        interest_rate REAL NOT NULL,
        tenure_years INTEGER NOT NULL,
        application_date TIMESTAMPTZ DEFAULT NOW()
    );
    """
    
    conn = None
    cursor = None
    
    try:
        # 3. Connect and create the table
        print("Connecting to database...")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        print("Connection successful.")
        
        cursor.execute(create_table_sql)
        conn.commit()
        print("Table 'applications2' created successfully (or already exists).")
            
    except psycopg2.Error as e:
        print(f"An error occurred with the database: {e}")
        if conn: conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
        print("Database connection closed.")

# --- Make sure to call your new function ---
if __name__ == "__main__":# This is your existing function
    create_applications_table() # This is the new one