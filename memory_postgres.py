import psycopg2
from langchain_community.chat_message_histories import SQLChatMessageHistory

POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "chat_history_db",
    "user": "postgres",
    "password": "postgres"
}

POSTGRES_CONNECTION_STRING = (
    f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}"
    f"@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"
)

def get_session_history(session_id: str) -> SQLChatMessageHistory:
    # Get PostgreSQL-backed chat history for a session
    return SQLChatMessageHistory(
        session_id=session_id,
        connection=POSTGRES_CONNECTION_STRING,
        table_name="message_store"  
    )

def clear_session_history(session_id: str = None):
    # Clear chat history for a specific session or all sessions
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        if session_id:
            # Clear specific session
            cursor.execute(
                "DELETE FROM message_store WHERE session_id = %s",  # Use %s for PostgreSQL
                (session_id,)
            )
            rows_deleted = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            if rows_deleted > 0:
                return f"Cleared {rows_deleted} messages for session: {session_id}"
            return f"No history for session: {session_id}"
        else:
            # Clear all sessions
            cursor.execute("DELETE FROM message_store")
            rows_deleted = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            return f"Cleared all chat histories ({rows_deleted} messages)"
            
    except psycopg2.Error as e:
        return f"Database error clearing history: {str(e)}"
    except Exception as e:
        return f"Other Error clearing history: {str(e)}"

