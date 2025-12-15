from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse

import asyncio
import json
import uvicorn

from main import run_agent
from memory_postgres import clear_session_history # PostgreSQL version

from pii_guardrail import OutputGuardrails
from prompt_guardrail import InputGuardrails

# Initialize guardrails
input_guardrails = InputGuardrails()
output_guardrails = OutputGuardrails()

app = FastAPI(title="AI Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# HTML content embedded in Python
HTML_CONTENT ="""
<!DOCTYPE html>
<html>
<head>
    <title>Senthu's AI Agent Chat</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        h1 {
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }
        .logo {
            width: 50px;
            height: 50px;
        }
        #chat-box {
            border: 1px solid #444;
            height: 1000px;
            overflow-y: auto;
            padding: 10px;
            margin-bottom: 10px;
            background-color: #2d2d2d;
        }
        .message {
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
        }
        .user {
            background-color: #1976d2;
            text-align: right;
            color: #ffffff;
        }
        .agent {
            background-color: #424242;
            color: #e0e0e0;
        }
        input {
            width: 100%;
            padding: 10px;
            box-sizing: border-box;
            background-color: #2d2d2d;
            border: 1px solid #444;
            color: #e0e0e0;
        }
        input::placeholder {
            color: #888;
        }
        input:focus {
            outline: none;
            border-color: #1976d2;
        }
    </style>
</head>
<body>
    <h1>
        <img src="data:image/png;base64,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" 
        alt="Logo" class="logo">
        Senthu's AI Agent Chat
    </h1>
    <div id="chat-box"></div>
    <input type="text" id="user-input" placeholder="Type your message...">
    <script>
        const sessionId = "web_user_" + Date.now();
        let ws = null;
        // REST API version
        async function sendMessage() {
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            if (!message) return;
            addMessage('user', message);
            input.value = '';
            try {
                const response = await fetch('http://localhost:8000/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message,
                        session_id: sessionId
                    })
                });
                const data = await response.json();
                if (response.ok) {
                    addMessage('agent', data.response);
                } else {
                    addMessage('agent', 'Error: ' + JSON.stringify(data.detail));
                }
            } catch (error) {
                addMessage('agent', 'Error: ' + error.message);
            }
        }
        // WebSocket version
        function connectWebSocket() {
            ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
            ws.onopen = () => {
                console.log('WebSocket connected');
                addMessage('agent', 'AI Agent Initiated! Type and press Enter.');
            };
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                addMessage('agent', data.response || data.error);
            };
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                addMessage('agent', 'Error: Cannot connect to WebSocket server. Make sure the backend is running on localhost:8000');
            };
            ws.onclose = (event) => {
                console.log('WebSocket closed:', event);
                addMessage('agent', 'Connection closed. Please refresh the page to reconnect.');
            };
            // Send message on Enter key
            document.getElementById('user-input').onkeypress = function(e) {
                if (e.key === 'Enter' && ws && ws.readyState === WebSocket.OPEN) {
                    const message = this.value.trim();
                    if (message) {
                        addMessage('user', message);
                        ws.send(JSON.stringify({
                            message
                        }));
                        this.value = '';
                    }
                }
            };
        }
        function addMessage(sender, text) {
            const chatBox = document.getElementById('chat-box');
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${sender}`;
            msgDiv.textContent = text;
            chatBox.appendChild(msgDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        
        // Auto-connect WebSocket when page loads
        window.onload = function() {
            connectWebSocket();
        };
    </script>
</body>
</html>
"""

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    return HTML_CONTENT

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # Input guardrail check
    passed, results = input_guardrails.check_all(request.message)
    print(f"Overall Input Guardrail Result: {'PASSED' if passed else 'FAILED'}")
    for result in results:
        print(f" - {result['cause']} (Risk: {result['risk_level']})")
    if not passed:
        detail = {
            "message": "Input blocked by guardrails",
            "violations": [{"cause": r["cause"], "risk_level": r["risk_level"]} for r in results]
        }
        raise HTTPException(status_code=400, detail=detail)
    else:
        print("Input passed all guardrail checks.")
        # Run agent (make it async-compatible)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, run_agent, request.message, request.session_id)
    
    return ChatResponse(response=response, session_id=request.session_id)

# WebSocket endpoint for streaming
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Parse JSON if needed
            try:
                message_data = json.loads(data)
                user_message = message_data.get("message", data)
            except:
                user_message = data
            
            # Input guardrail check
            passed, results = input_guardrails.check_all(user_message)
            if not passed:
                await websocket.send_json({
                    "error": "Input blocked by guardrails",
                    "violations": [{"cause": r["cause"], "risk_level": r["risk_level"]} for r in results]
                })
                continue
            
            # Process with agent
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, run_agent, user_message, session_id)
            
            # Send response
            await websocket.send_json({
                "response": response,
                "session_id": session_id
            })
    
    except WebSocketDisconnect:
        print(f"Client disconnected: {session_id}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Clear session endpoint
@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    success = clear_session_history(session_id)
    if success:
        return {"message": f"Session {session_id} cleared"}
    else:
        return {"message": f"No history found for session {session_id}"}

# List sessions endpoint (if your get_session_history supports it)
@app.get("/sessions")
async def list_sessions():
    # You may need to modify get_session_history to return session list
    return {"sessions": ["Add your session listing logic here"]}

if __name__ == "__main__":
    print("API is running on http://localhost:8000")# Import your existing agent code
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
