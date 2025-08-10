#!/usr/bin/env python3
"""
Direct test of Ollama API connection
"""
import asyncio
import httpx
import json

async def test_ollama():
    """Test Ollama API directly"""
    try:
        client = httpx.AsyncClient(timeout=30.0)
        
        # Test basic connection
        print("Testing Ollama connection...")
        response = await client.get("http://localhost:11434/api/tags")
        print(f"Connection test: {response.status_code}")
        
        # Test chat API
        print("\nTesting chat API...")
        payload = {
            "model": "llama3.1:8b",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, can you help with restaurant bookings?"}
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 100
            }
        }
        
        print(f"Sending payload: {json.dumps(payload, indent=2)}")
        
        response = await client.post(
            "http://localhost:11434/api/chat",
            json=payload
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {result['message']['content']}")
        else:
            print(f"Error response: {response.text}")
            
        await client.aclose()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_ollama())
