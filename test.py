import requests

# Test chat endpoint
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "This is the email address senthu@gmail.com. Can you find it?",
        "session_id": "test_user"
    }
)
print(response.json())