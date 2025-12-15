import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# First, install: pip install psycopg2-binary --break-system-packages
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",  # Default admin user
    password="postgres"
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()

# Create the database
try:
    cursor.execute("CREATE DATABASE monitor_history_db;") # Change databvase name if needed
    print("Database 'monitor_history_db' created successfully")
except psycopg2.errors.DuplicateDatabase:
    print("Database 'monitor_history_db' already exists")

# Create the user
try:
    cursor.execute("CREATE USER monitor_user WITH PASSWORD 'monitor_password';") # Change username and password if needed
    print("User 'monitor_user' created successfully")
except psycopg2.errors.DuplicateObject:
    print("User 'monitor_user' already exists")

# Grant privileges
cursor.execute("GRANT ALL PRIVILEGES ON DATABASE monitor_history_db TO monitor_user;") # Change privilege if needed
print("Privileges granted to 'monitor_user'")

# Close connection
cursor.close()
conn.close()

print("Setup complete!")