import psycopg2
from tabulate import tabulate

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "postgres",
    "database": "phoenix_db"
}

def list_tables():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    cursor.close()
    conn.close()
    
    print("\nAvailable Tables:")
    print("="*50)
    for table in tables:
        print(f"  • {table[0]}")
    print()
    
    return [t[0] for t in tables]

def view_table(table_name, limit=100):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get column names
    cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    columns = [col[0] for col in cursor.fetchall()]
    
    # Get data
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit};")
    rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Display
    print(f"\n Table: {table_name}")
    print(f"   Rows: {len(rows)} (showing up to {limit})")
    print("="*80)
    print(tabulate(rows, headers=columns, tablefmt="grid"))
    print()

def table_info(table_name):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    
    schema = cursor.fetchall()
    cursor.close()
    conn.close()
    
    print(f"\n🔍 Schema for: {table_name}")
    print("="*80)
    print(tabulate(
        schema, 
        headers=["Column", "Type", "Max Length", "Nullable", "Default"],
        tablefmt="grid"
    ))
    print()

if __name__ == "__main__":
    # List all tables
    tables = list_tables()
    
    # View each table
    for table in tables:
        table_info(table)
        view_table(table, limit=25)