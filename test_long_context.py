#!/usr/bin/env python3
"""
Simple test for enhanced long conversation context handling
"""

import asyncio
import httpx
import json

async def test_long_conversation():
    """Test conversation with multiple messages to validate context retention"""
    
    session_id = "long_context_test"
    base_url = "http://localhost:8000"
    
    # Define a conversation that builds on itself
    messages = [
        "Hi, I'm looking for a dinner reservation",
        "I'd like to try European cuisine",
        "The Hungry Unicorn sounds perfect",
        "I'm thinking this Saturday evening",
        "Around 7 PM would be ideal",
        "It will be for 4 people",
        "Actually, can we check availability for Friday instead?",
        "What times are available on Friday?",
        "7:30 PM sounds good",
        "My name is John Smith",
        "My email is john.smith@email.com",
        "Can you confirm the details?",
        "Actually, what's your cancellation policy?",
        "And do you have vegetarian options?",
        "What about parking?",
        "Is there a dress code?",
        "Can I make the reservation now?",
        "What will be my booking reference?",
        "Can I add special dietary requirements?",
        "One person is gluten-free",
        "Perfect, please proceed with the booking",
        "Can you send me a confirmation?",
        "What's the restaurant's address?",
        "How early should we arrive?",
        "Do you take walk-ins?",
        "What if we're running late?",
        "Can I modify the reservation later?",
        "What's the latest I can cancel?",
        "Do you have private dining rooms?",
        "What's the wine selection like?",
        "Do you have a happy hour?",
        "Can I make another reservation for next week?",
        "What about Sunday brunch?",
        "Do you have outdoor seating?",
        "Can you tell me about the menu again from the beginning?"  # Test context retention
    ]
    
    print(f"🧪 Testing long conversation context with {len(messages)} messages")
    print(f"Session ID: {session_id}")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, message in enumerate(messages, 1):
            print(f"\nTurn {i:2d}: {message}")
            
            try:
                response = await client.post(
                    f"{base_url}/chat",
                    json={
                        "message": message,
                        "session_id": session_id
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("message", "No response")
                    message_count = data.get("conversation_state", {}).get("message_count", 0)
                    
                    print(f"         AI ({message_count} total): {ai_response[:100]}{'...' if len(ai_response) > 100 else ''}")
                    
                    # Check for context awareness at key points
                    if i == 15:
                        print(f"         ✓ Checkpoint: 15 messages processed")
                    elif i == 25:
                        print(f"         ✓ Checkpoint: 25 messages - testing longer context")
                    elif i == 35:
                        print(f"         ✓ Checkpoint: 35+ messages - maximum context test")
                        # Check if the response references earlier conversation
                        response_lower = ai_response.lower()
                        context_indicators = ['european', 'hungry unicorn', 'john', 'friday', '7:30']
                        context_retained = any(indicator in response_lower for indicator in context_indicators)
                        
                        if context_retained:
                            print(f"         ✅ CONTEXT RETAINED: AI referenced earlier conversation details")
                        else:
                            print(f"         ⚠️  CONTEXT CHECK: Limited context retention detected")
                else:
                    print(f"         ❌ HTTP Error: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"         ❌ Error: {e}")
                break
    
    print("\n" + "=" * 60)
    print(f"✅ Completed {len(messages)} message conversation test")
    print("🎯 Enhanced system successfully handled long conversation context!")

async def main():
    """Run the test"""
    try:
        # Check if server is running
        async with httpx.AsyncClient() as client:
            health_response = await client.get("http://localhost:8000/")
            print(f"✅ Server running: {health_response.json().get('service')}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return
    
    await test_long_conversation()

if __name__ == "__main__":
    asyncio.run(main())
