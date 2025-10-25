import os
import psycopg2
from dotenv import load_dotenv

def setup_database():
    load_dotenv('api_secret.env')

    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_NAME = os.environ.get("DB_NAME")

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS customers (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT NOT NULL UNIQUE,
        address TEXT NOT NULL,
        pre_approved_limit INTEGER NOT NULL,
        credit_score INTEGER NOT NULL
    );
    """

    mock_data = [
        ('Priya Sharma', '9876543210', '123 MG Road, Bangalore', 50000, 780),
        ('Rohan Gupta', '1234567890', '456 Main St, Delhi', 25000, 650),
        ('Amit Singh', '5555544444', '789 Park Ave, Mumbai', 100000, 820),
        ('Sneha Reddy', '8888899999', '101 Jubilee Hills, Hyderabad', 75000, 790),
        ('Vikram Kumar', '7777766666', '202 Anna Salai, Chennai', 30000, 680),
        ('Ananya Bose', '6666655555', '303 Salt Lake, Kolkata', 150000, 850),
        ('David Lee', '9999911111', 'A-14 Koregaon Park, Pune', 40000, 710),
        ('Zara Khan', '3333322222', 'B-7, Sector 18, Noida', 90000, 760),
        ('Karan Malhotra', '2222211111', '505 Linking Road, Mumbai', 120000, 810),
        ('Nisha Patel', '4444455555', 'C-9, CG Road, Ahmedabad', 20000, 620)
    ]

    try:
        # 4. Connect to the database
        print(f"Connecting to database at {DB_HOST}:{DB_PORT} as user {DB_USER}...")
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
        print("Table 'customers' created successfully (or already exists).")
        
        # 6. Check if table is already populated
        cursor.execute("SELECT COUNT(*) FROM customers")
        count = cursor.fetchone()[0]

        if count == 0:
            # 7. Insert the data
            # %s is the placeholder for psycopg2
            insert_query = """
            INSERT INTO customers (name, phone, address, pre_approved_limit, credit_score) 
            VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_query, mock_data)
            conn.commit()
            print(f"Successfully inserted {len(mock_data)} mock users.")
        else:
            print("Table 'customers' already contains data. No new data inserted.")
            
    except psycopg2.Error as e:
        print(f"An error occurred with the database: {e}")
        if conn:
            conn.rollback() # Roll back any changes if an error occurs
            
    finally:
        # 8. Always close connections
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    setup_database()