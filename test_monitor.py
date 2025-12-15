# test_postgres.py
import psycopg2

# Test your PostgreSQL connection
DB_URL = "postgresql://monitor_user:monitor_password@localhost:5432/monitor_history_db"

try:
    conn = psycopg2.connect(DB_URL)
    print("PostgreSQL connection successful!")
    conn.close()
except Exception as e:
    print(f"PostgreSQL connection failed: {e}")
    print("\nMake sure:")
    print("  1. PostgreSQL is running")
    print("  2. Database exists")
    print("  3. User has permissions")