#!/usr/bin/env python3
"""
TableBooker AI Agent - User Stories Test Script

Tests all core user stories with simple HTTP requests
"""

import requests
import json
import time
from datetime import datetime, timedelta

class UserStoriesTest:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = f"test_{int(time.time())}"
        self.booking_reference = None
        
    def send_message(self, message):
        """Send a message to the chat endpoint"""
        print(f"\n🧑‍💬 USER: {message}")
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    "message": message,
                    "session_id": self.session_id
                },
                timeout=300  # Allow long, complete responses without cutting off
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    def print_test_result(self, story, message, response):
        """Print formatted test result with full AI message, showing extracted intent only"""
        print(f"\n{'='*60}")
        print(f"🧪 {story}")
        print(f"📤 REQUEST: {message}")

        # Show extracted intent (if returned by API)
        intent = response.get('intent')
        if intent:
            print("🧭 EXTRACTED INTENT:\n" + json.dumps(intent, indent=2, ensure_ascii=False))

        # Print full assistant message without truncation
        assistant_message = response.get('message', 'No message')
        print("🤖 RESPONSE (full):\n" + (assistant_message if isinstance(assistant_message, str) else json.dumps(assistant_message, ensure_ascii=False)))
        
        if response.get('error'):
            print(f"\n❌ ERROR: {response['error']}")
        
        print(f"{'='*60}")
        return response
    
    def test_story_1_availability(self):
        """Test User Story 1: Check availability"""
        print("\n🎯 USER STORY 1: CHECK AVAILABILITY")
        print("User story: As a user, I would like to check availability for a specific date and time")
        
        # Natural availability check
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        message = (
            f"Hey! We're thinking of dinner on {tomorrow}. "
            "Do you have any tables for 2 around 7pm? "
            "If there's Japanese cuisine available, that would be great."
        )
        response = self.send_message(message)
        return self.print_test_result("Check Availability (Natural Query)", message, response)
    
    def test_story_2_booking(self):
        """Test User Story 2: Book a reservation"""
        print("\n🎯 USER STORY 2: BOOK A RESERVATION")
        print("User story: As a user, I would like to book a reservation by specifying details")
        
        # Natural booking message
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        message = (
            f"Could you please book a table at Pizza Palace for 2 people on {tomorrow} "
            "around 7pm? My name is John Smith and you can reach me at john@example.com."
        )
        response = self.send_message(message)
        result = self.print_test_result("Create Booking (Natural Query)", message, response)
        
        # Extract booking reference if successful
        if result.get('booking_data') and result['booking_data'].get('reference'):
            self.booking_reference = result['booking_data']['reference']
            print(f"✅ Booking Reference Saved: {self.booking_reference}")
        
        return result
    
    def test_story_3_check_booking(self):
        """Test User Story 3: Check existing booking details"""
        print("\n🎯 USER STORY 3: CHECK RESERVATION INFORMATION")
        print("User story: As a user, I would like to check my reservation information using my booking reference")
        
        if not self.booking_reference:
            print("⚠️ No booking reference available, using test reference")
            self.booking_reference = "GYXUK87"  # Use a test reference
        
        message = (
            f"Could you check my reservation for me? The reference is {self.booking_reference}. "
            "I just want to confirm the time and restaurant."
        )
        response = self.send_message(message)
        return self.print_test_result("Check Booking Details (Natural Query)", message, response)
    
    def test_story_4_modify_booking(self):
        """Test User Story 4: Modify a reservation"""
        print("\n🎯 USER STORY 4: MODIFY A RESERVATION") 
        print("User story: As a user, I would like to modify my reservation")
        
        if not self.booking_reference:
            print("⚠️ No booking reference available for modification test")
            return {"error": "No booking reference"}
        
        # Natural modification message
        message = (
            f"Actually, can we move my reservation {self.booking_reference} to 8pm instead?"
        )
        response = self.send_message(message)
        result = self.print_test_result("Modify Booking Time (Natural Query)", message, response)
        
        # Natural cancellation message
        message = f"On second thought, please cancel that booking {self.booking_reference}."
        response = self.send_message(message)
        self.print_test_result("Cancel Booking (Natural Query)", message, response)
        
        return result
    
    def test_edge_cases_cancelled_booking(self):
        """Test Edge Cases: Cancelled booking status handling"""
        print("\n🎯 EDGE CASES: CANCELLED BOOKING STATUS")
        print("Testing booking status edge cases and prevention logic")
        
        # Create a new booking specifically for cancellation testing (natural phrasing)
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        message = (
            f"Could you set up a booking at Cafe Bistro on {tomorrow} at 5pm for three people? "
            "Name is Test User, email is test@example.com."
        )
        response = self.send_message(message)
        result = self.print_test_result("Create Test Booking for Cancellation (Natural)", message, response)
        
        # Extract booking reference for cancellation tests
        test_booking_ref = None
        if result.get('booking_data') and result['booking_data'].get('reference'):
            test_booking_ref = result['booking_data']['reference']
            print(f"✅ Test Booking Reference: {test_booking_ref}")
        else:
            print("⚠️ Could not create test booking for edge case testing")
            return {"error": "No test booking created"}
        
        # Test 1: Cancel the booking
        message = f"Please cancel my reservation {test_booking_ref}."
        response = self.send_message(message)
        self.print_test_result("Cancel Test Booking (Natural)", message, response)
        
        # Test 2: Check cancelled booking status
        message = f"Can you check the status of my booking {test_booking_ref}?"
        response = self.send_message(message)
        self.print_test_result("Check Cancelled Booking Status (Natural)", message, response)
        
        # Test 3: Try to modify cancelled booking (should be blocked)
        message = f"Could you change my booking {test_booking_ref} to 7pm?"
        response = self.send_message(message)
        self.print_test_result("Try to Modify Cancelled Booking (Should Block)", message, response)
        
        # Test 4: Try to cancel already cancelled booking (should be blocked)
        message = f"I want to cancel {test_booking_ref} again."
        response = self.send_message(message)
        self.print_test_result("Try to Cancel Already Cancelled Booking (Should Block)", message, response)
        
        # Test 5: Check cancelled booking status again
        message = f"Could you confirm the details for booking {test_booking_ref}?"
        response = self.send_message(message)
        self.print_test_result("Re-check Cancelled Booking Status (Natural)", message, response)
        
        return {"test_booking_ref": test_booking_ref, "completed": True}
    
    def test_edge_cases_invalid_operations(self):
        """Test Edge Cases: Invalid operations and error handling"""
        print("\n🎯 EDGE CASES: INVALID OPERATIONS")
        print("Testing invalid booking references and error scenarios")
        
        # Test 1: Check non-existent booking reference
        message = "Can you look up my booking with reference INVALID123?"
        response = self.send_message(message)
        self.print_test_result("Check Invalid Booking Reference (Natural)", message, response)
        
        # Test 2: Try to modify non-existent booking
        message = "Could you move booking NOTFOUND456 to 8pm?"
        response = self.send_message(message)
        self.print_test_result("Try to Modify Non-existent Booking (Natural)", message, response)
        
        # Test 3: Try to cancel non-existent booking
        message = "Please cancel booking MISSING789."
        response = self.send_message(message)
        self.print_test_result("Try to Cancel Non-existent Booking (Natural)", message, response)
        
        # Test 4: Ambiguous booking request
        message = "We'd like to book a table."
        response = self.send_message(message)
        self.print_test_result("Incomplete Booking Request (Natural)", message, response)
        
        # Test 5: Invalid date request
        message = "Do you have anything for two on February 30th?"
        response = self.send_message(message)
        self.print_test_result("Invalid Date Request (Natural)", message, response)
        
        return {"completed": True}
    
    def test_system_health(self):
        """Test system health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ System Health Check: PASSED")
                print(f"   - Details: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"❌ System Health Check: FAILED - HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ System Health Check: FAILED - {e}")
            return False
    
    def run_all_tests(self):
        """Run all user story tests"""
        print("🚀 Starting TableBooker AI Agent User Stories Test")
        print(f"📡 Testing against: {self.base_url}")
        print(f"🆔 Session ID: {self.session_id}")
        
        # Health check
        if not self.test_system_health():
            print("❌ Cannot proceed - system unhealthy")
            return False
        
        try:
            # Run all user stories
            self.test_story_1_availability()
            self.test_story_2_booking()
            self.test_story_3_check_booking()
            self.test_story_4_modify_booking()
            
            # Run edge case tests
            self.test_edge_cases_cancelled_booking()
            self.test_edge_cases_invalid_operations()
            
            print("\n🎉 USER STORIES AND EDGE CASES TESTING COMPLETED!")
            print(f"📋 Final booking reference: {self.booking_reference or 'None'}")
            return True
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            return False
 

def main():
    """Main test runner"""
    tester = UserStoriesTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All user stories tested successfully!")
    else:
        print("\n❌ Some tests encountered issues!")
 
if __name__ == "__main__":
    main()
