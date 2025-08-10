"""
Quick test script for Ollama integration
"""
import requests
import json

def test_ollama_chat():
    """Test the Ollama chat functionality"""
    try:
        chat_request = {
            "message": "Hello! I want to book a table for 2 people tomorrow at 7pm",
            "session_id": "test-ollama"
        }
        
        print("🤖 Testing Ollama AI Chat...")
        print(f"📝 Sending: {chat_request['message']}")
        
        response = requests.post(
            "http://localhost:8000/chat",
            json=chat_request,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI Response: {data['message']}")
            print(f"💡 Suggestions: {data.get('suggestions', [])}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_ollama_status():
    """Test Ollama connection"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"🏥 Health: {data}")
            return data.get('ai_provider') == 'Ollama'
        return False
    except:
        return False

if __name__ == "__main__":
    print("🦙 Testing Ollama Integration")
    print("=" * 40)
    
    if test_ollama_status():
        print("✅ Ollama backend detected")
        if test_ollama_chat():
            print("🎉 Ollama integration working!")
        else:
            print("⚠️ Chat test failed")
    else:
        print("❌ Ollama backend not running")
        print("Make sure to:")
        print("1. Run: ollama serve")
        print("2. Run: python main_ollama.py")
