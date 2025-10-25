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
    CREATE TABLE IF NOT EXISTS loan_options (
        id SERIAL PRIMARY KEY,
        plan_name TEXT NOT NULL,
        min_score INTEGER NOT NULL,
        max_score INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        interest_rate INTEGER NOT NULL,
        tenure_years INTEGER NOT NULL
    );
    """

    # (plan_name, min_score, max_score, amount, interest_rate, tenure_years)
    loan_data = [
        ('Credit Builder Loan', 600, 649, 10000, 18.5, 2),
        ('Fresh Start Plan', 600, 649, 15000, 17.0, 3),
        ('Small Emergency Loan', 600, 679, 5000, 22.0, 1),
        ('Basic Consolidation', 620, 699, 25000, 15.5, 5),
        ('Fair Credit Plan', 650, 699, 20000, 14.0, 3),
        ('Appliance Loan', 650, 699, 7000, 13.5, 2),
        ('Moving Expenses Loan', 670, 729, 12000, 12.0, 3),
        ('Standard Personal Loan', 680, 739, 30000, 11.5, 4),
        ('Good Credit Plan', 700, 749, 50000, 9.5, 5),
        ('Car Repair Loan', 700, 749, 10000, 8.9, 2),
        ('Home Renovation Lite', 720, 799, 60000, 7.8, 7),
        ('Wedding Plan', 720, 799, 40000, 8.2, 5),
        ('Prime Loan', 750, 900, 100000, 6.0, 5),
        ('Elite Loan', 780, 900, 150000, 5.5, 7),
        ('Premier Debt Consolidation', 750, 900, 120000, 5.9, 5),
        ('Investment Starter', 800, 900, 200000, 4.8, 3),
        ('Quick Cash (High Interest)', 600, 900, 2000, 25.0, 1),
        ('Holiday Loan', 680, 900, 8000, 9.0, 2),
        ('Education Top-Up', 700, 900, 35000, 7.5, 4),
        ('Large Project Loan', 740, 900, 250000, 5.2, 10)
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
        print("Table 'loan_options' created successfully (or already exists).")
        
        # 6. Check if table is already populated
        cursor.execute("SELECT COUNT(*) FROM loan_options")
        count = cursor.fetchone()[0]

        if count == 0:
            # 7. Insert the data
            # %s is the placeholder for psycopg2
            insert_query = """
            INSERT INTO loan_options (plan_name, min_score, max_score, amount, interest_rate, tenure_years) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cursor.executemany(insert_query, loan_data)
            conn.commit()
            print(f"Successfully inserted {len(loan_data)} mock users.")
        else:
            print("Table 'loan_options' already contains data. No new data inserted.")
            
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