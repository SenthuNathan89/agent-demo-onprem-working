import uvicorn
import webbrowser
import threading
import time

def open_browser():
    """Open browser after server starts"""
    time.sleep(3)  # Wait for server to fully start
    webbrowser.open("http://localhost:8000")

def run_server():
    """Run the FastAPI server"""
    print("🚀 Starting AI Agent API...")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    # Start browser opener in background thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Run server (blocking)
    run_server()
    