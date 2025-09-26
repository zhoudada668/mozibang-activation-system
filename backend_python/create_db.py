import pymysql
import os

# Database configuration (same as in app.py)
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'Sn730080')
MYSQL_DB = os.environ.get('MYSQL_DB', 'mozibang')

def create_database_and_table():
    try:
        # Connect to MySQL server (without specifying a database initially)
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()

        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
        print(f"Database '{MYSQL_DB}' ensured to exist.")

        # Connect to the newly created/existing database
        conn.select_db(MYSQL_DB)

        # Create licenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                license_key VARCHAR(255) NOT NULL UNIQUE,
                is_active BOOLEAN DEFAULT TRUE,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                activated_at DATETIME
            )
        """)
        print("Table 'licenses' ensured to exist.")

        conn.commit()
    except Exception as e:
        print(f"Error creating database or table: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

if __name__ == '__main__':
    create_database_and_table()