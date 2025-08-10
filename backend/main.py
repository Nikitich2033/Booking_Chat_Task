"""
TableBooker AI Agent Backend with Ollama Integration
"""
import asyncio
import uuid
import httpx
import re
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Simple models for Ollama integration
class ChatRequest(BaseModel):
    message: str
    session_id: str = None
    user_id: str = None
    context: Dict[str, Any] = {}

class ChatResponse(BaseModel):
    message: str
    session_id: str
    suggestions: list = []
    conversation_state: Dict[str, Any] = {}
    booking_data: Optional[Dict[str, Any]] = None
    availability_data: Optional[Dict[str, Any]] = None

# Create FastAPI app
app = FastAPI(
    title="TableBooker AI Agent API (Ollama)",
    description="Restaurant booking with Ollama AI integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.1:8b"

# Booking API configuration
BOOKING_API_BASE_URL = "http://localhost:8547"
RESTAURANT_NAME = "TheHungryUnicorn"
BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFwcGVsbGErYXBpQHJlc2RpYXJ5LmNvbSIsIm5iZiI6MTc1NDQzMDgwNSwiZXhwIjoxNzU0NTE3MjA1LCJpYXQiOjE3NTQ0MzA4MDUsImlzcyI6IlNlbGYiLCJhdWQiOiJodHRwczovL2FwaS5yZXNkaWFyeS5jb20ifQ.g3yLsufdk8Fn2094SB3J3XW-KdBc0DY9a2Jiu_56ud8"

# Simple in-memory storage
sessions = {}

# Booking API Functions
class BookingAPIClient:
    """Client for interacting with the restaurant booking API"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = BOOKING_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    def _normalize_time_to_hhmmss(self, time_str: str) -> str:
        """Convert various time formats to HH:MM:SS format required by API"""
        from datetime import datetime
        
        time_lower = time_str.lower().strip()
        
        # Handle formats like "7pm", "7:30pm", "19:00", "7:30", etc.
        if ':' in time_lower:
            # Format: "7:30pm" or "19:30"
            base_time = time_lower.replace('pm', '').replace('am', '').strip()
            try:
                if 'pm' in time_lower:
                    hour, minute = base_time.split(':')
                    hour = int(hour)
                    if hour != 12:
                        hour += 12
                    return f"{hour:02d}:{int(minute):02d}:00"
                elif 'am' in time_lower:
                    hour, minute = base_time.split(':')
                    hour = int(hour)
                    if hour == 12:
                        hour = 0
                    return f"{hour:02d}:{int(minute):02d}:00"
                else:
                    # 24-hour format like "19:30"
                    hour, minute = base_time.split(':')
                    return f"{int(hour):02d}:{int(minute):02d}:00"
            except ValueError:
                pass
        else:
            # Format: "7pm" or "19"
            try:
                base_time = time_lower.replace('pm', '').replace('am', '').strip()
                hour = int(base_time)
                
                if 'pm' in time_lower and hour != 12:
                    hour += 12
                elif 'am' in time_lower and hour == 12:
                    hour = 0
                
                return f"{hour:02d}:00:00"
            except ValueError:
                pass
        
        # Default fallback - assume it's already in correct format or use 19:00
        if time_str.count(':') == 2:
            return time_str
        else:
            return "19:00:00"  # Default to 7pm
    
    async def check_availability(self, date: str, party_size: int) -> dict:
        """Check table availability for given date and party size"""
        try:
            data = {
                "VisitDate": date,
                "PartySize": str(party_size),
                "ChannelCode": "ONLINE"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/ConsumerApi/v1/Restaurant/{RESTAURANT_NAME}/AvailabilitySearch",
                data=data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Failed to check availability: {str(e)}"}
    
    async def create_booking(self, date: str, time: str, party_size: int, customer_info: dict) -> dict:
        """Create a new booking"""
        try:
            from datetime import datetime
            
            # Parse date - expect YYYY-MM-DD format
            visit_date = datetime.strptime(date, '%Y-%m-%d').date()
            
            # Parse time to HH:MM:SS format required by API
            visit_time_str = self._normalize_time_to_hhmmss(time)
            
            # Prepare data according to API specification
            data = {
                "VisitDate": visit_date.isoformat(),  # YYYY-MM-DD
                "VisitTime": visit_time_str,          # HH:MM:SS
                "PartySize": str(party_size),         # Convert to string
                "ChannelCode": "ONLINE"
            }
            
            # Add customer information with correct API field names
            if customer_info.get("name"):
                name_parts = customer_info["name"].strip().split(" ", 1)
                data["Customer[FirstName]"] = name_parts[0]
                if len(name_parts) > 1:
                    data["Customer[Surname]"] = name_parts[1]
                else:
                    data["Customer[Surname]"] = ""  # Provide empty surname if only one name
            
            if customer_info.get("email"):
                data["Customer[Email]"] = customer_info["email"]
            
            if customer_info.get("phone"):
                data["Customer[Mobile]"] = customer_info["phone"]
            
            if customer_info.get("special_requests"):
                data["SpecialRequests"] = customer_info["special_requests"]
            
            print(f"Creating booking with data: {data}")
            
            response = await self.client.post(
                f"{self.base_url}/api/ConsumerApi/v1/Restaurant/{RESTAURANT_NAME}/BookingWithStripeToken",
                data=data,
                headers=self.headers
            )
            
            print(f"Booking API response: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"Parsed booking response: {response_data}")
                return response_data
            elif response.status_code == 201:
                # Some APIs return 201 for created resources
                response_data = response.json()
                print(f"Parsed booking response (201): {response_data}")
                return response_data
            else:
                error_msg = f"API error: {response.status_code} - {response.text}"
                print(f"Booking API error: {error_msg}")
                return {"error": error_msg}
                
        except Exception as e:
            print(f"Booking creation error: {e}")
            return {"error": f"Failed to create booking: {str(e)}"}
    
    async def get_booking(self, booking_reference: str) -> dict:
        """Get booking details by reference"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/ConsumerApi/v1/Restaurant/{RESTAURANT_NAME}/Booking/{booking_reference}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Failed to get booking: {str(e)}"}

    async def cancel_booking(self, booking_reference: str, microsite_name: str = None, cancellation_reason_id: int = 1) -> dict:
        """Cancel an existing booking"""
        try:
            data = {
                "micrositeName": microsite_name or RESTAURANT_NAME,
                "bookingReference": booking_reference,
                "cancellationReasonId": cancellation_reason_id,
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/ConsumerApi/v1/Restaurant/{RESTAURANT_NAME}/Booking/{booking_reference}/Cancel",
                data=data,
                headers=self.headers,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Failed to cancel booking: {str(e)}"}

    async def update_booking(self, booking_reference: str, *, date: Optional[str] = None, time: Optional[str] = None,
                              party_size: Optional[int] = None, special_requests: Optional[str] = None,
                              is_leave_time_confirmed: Optional[bool] = None) -> dict:
        """Update an existing booking"""
        try:
            from datetime import datetime
            data: Dict[str, Any] = {}

            if date:
                # Expect YYYY-MM-DD
                visit_date = datetime.strptime(date, '%Y-%m-%d').date()
                data["VisitDate"] = visit_date.isoformat()

            if time:
                # Use the same time normalization method
                data["VisitTime"] = self._normalize_time_to_hhmmss(time)

            if party_size is not None:
                data["PartySize"] = party_size

            if special_requests is not None:
                data["SpecialRequests"] = special_requests

            if is_leave_time_confirmed is not None:
                data["IsLeaveTimeConfirmed"] = is_leave_time_confirmed

            response = await self.client.patch(
                f"{self.base_url}/api/ConsumerApi/v1/Restaurant/{RESTAURANT_NAME}/Booking/{booking_reference}",
                data=data,
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code} - {response.text}"}
        except Exception as e:
            return {"error": f"Failed to update booking: {str(e)}"}

# Initialize booking API client
booking_client = BookingAPIClient()

class OllamaAI:
    """Simple Ollama AI integration"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=15.0, read=60.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        self.base_url = OLLAMA_BASE_URL
        self.model = MODEL_NAME
    
    def normalize_date_text(self, date_text: str) -> Optional[str]:
        """Normalize various date phrasings to YYYY-MM-DD"""
        if not date_text:
            return None
        txt = date_text.strip().lower()
        now = datetime.now()
        
        # Absolute formats
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                d = datetime.strptime(txt, fmt).date()
                return d.isoformat()
            except ValueError:
                pass
        
        # Relative keywords
        if txt == "today":
            return now.date().isoformat()
        if txt == "tomorrow":
            return (now + timedelta(days=1)).date().isoformat()
        
        # Month name + day
        for fmt in ("%B %d", "%b %d"):
            try:
                d = datetime.strptime(txt, fmt).replace(year=now.year).date()
                if d < now.date():
                    d = d.replace(year=now.year + 1)
                return d.isoformat()
            except ValueError:
                pass
        
        # Weekday handling
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        m = re.match(r"^(next\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$", txt)
        if m:
            add_week = 1 if m.group(1) else 0
            target = weekdays[m.group(2)]
            delta = (target - now.weekday()) % 7
            if delta == 0:
                delta = 7
            delta += add_week * 7
            d = (now + timedelta(days=delta)).date()
            return d.isoformat()
        
        return None
    
    def _parse_time_to_24h(self, time_str: str) -> str:
        """Parse time string to 24-hour format for comparison"""
        try:
            time_lower = time_str.lower().strip()
            
            if ':' in time_lower:
                # Handle "7:30pm" or "19:30"
                base_time = time_lower.replace('pm', '').replace('am', '').strip()
                if 'pm' in time_lower:
                    hour, minute = base_time.split(':')
                    hour = int(hour)
                    if hour != 12:
                        hour += 12
                    return f"{hour:02d}:{int(minute):02d}"
                elif 'am' in time_lower:
                    hour, minute = base_time.split(':')
                    hour = int(hour)
                    if hour == 12:
                        hour = 0
                    return f"{hour:02d}:{int(minute):02d}"
                else:
                    # Already in 24-hour format
                    hour, minute = base_time.split(':')
                    return f"{int(hour):02d}:{int(minute):02d}"
            else:
                # Handle "7pm" or "19"
                base_time = time_lower.replace('pm', '').replace('am', '').strip()
                hour = int(base_time)
                
                if 'pm' in time_lower and hour != 12:
                    hour += 12
                elif 'am' in time_lower and hour == 12:
                    hour = 0
                
                return f"{hour:02d}:00"
        except:
            return "19:00"  # Default fallback
    
    def _times_match(self, requested_time: str, slot_time: str) -> bool:
        """Check if requested time matches available slot (with some flexibility)"""
        try:
            # Extract hours and minutes
            req_parts = requested_time.split(':')
            slot_parts = slot_time.split(':')
            
            req_hour, req_min = int(req_parts[0]), int(req_parts[1])
            slot_hour, slot_min = int(slot_parts[0]), int(slot_parts[1])
            
            # Convert to minutes for easy comparison
            req_total_min = req_hour * 60 + req_min
            slot_total_min = slot_hour * 60 + slot_min
            
            # Allow 30-minute flexibility
            return abs(req_total_min - slot_total_min) <= 30
        except:
            return requested_time[:5] == slot_time[:5]  # Exact match fallback
    
    def _is_booking_confirmation(self, message: str, session_data: dict) -> bool:
        """Check if message is confirming a pending booking"""
        if not session_data.get('awaiting_confirmation'):
            return False
        
        confirmation_words = ['yes', 'confirm', 'book it', 'proceed', 'go ahead', 'that\'s correct', 'correct', 'ok', 'okay']
        return any(word in message.lower() for word in confirmation_words)
    
    def _is_direct_booking_command(self, message: str) -> bool:
        """Check if message is a direct booking command with all details"""
        msg_lower = message.lower()
        has_book_word = any(word in msg_lower for word in ['book', 'reserve', 'reservation'])
        has_people = any(word in msg_lower for word in ['people', 'guests', 'party'])
        has_name_indicator = any(word in msg_lower for word in ['name', 'i\'m', 'my name'])
        has_email = '@' in message or 'email' in msg_lower
        has_time = any(indicator in msg_lower for indicator in ['pm', 'am', ':', 'time', 'tomorrow', 'today'])
        
        print(f"Direct booking check: book={has_book_word}, people={has_people}, name={has_name_indicator}, email={has_email}, time={has_time}")
        return has_book_word and has_people and (has_name_indicator or has_email) and has_time
    
    def _has_all_booking_details(self, booking_data: dict) -> bool:
        """Check if booking data has all required fields"""
        required_fields = ['date', 'time', 'party_size', 'name', 'email']
        return all(booking_data.get(field) for field in required_fields)
    
    def _generate_confirmation_message(self, booking_data: dict) -> str:
        """Generate confirmation message for pending booking"""
        normalized_date = self.normalize_date_text(booking_data['date'])
        
        message = "🔄 **READY TO CONFIRM YOUR BOOKING**\n\n"
        message += "📋 **Please confirm these details:**\n"
        message += f"🍽️ Restaurant: TheHungryUnicorn\n"
        message += f"📅 Date: {normalized_date or booking_data['date']}\n"
        message += f"🕐 Time: {booking_data['time']}\n"
        message += f"👥 Party Size: {booking_data['party_size']} people\n"
        message += f"👤 Name: {booking_data['name']}\n"
        message += f"📧 Email: {booking_data['email']}\n"
        if booking_data.get('phone'):
            message += f"📞 Phone: {booking_data['phone']}\n"
        message += "\n✅ **Type 'YES' or 'CONFIRM' to book this reservation**\n"
        message += "❌ **Type 'NO' or 'CANCEL' to start over**"
        
        return message
    
    async def _handle_booking_confirmation(self, session_data: dict) -> Tuple[str, Optional[dict], Optional[dict], dict]:
        """Handle confirmed booking - bypass AI and go direct to API"""
        pending_booking = session_data.get('pending_booking', {})
        
        if not self._has_all_booking_details(pending_booking):
            session_data.pop('awaiting_confirmation', None)
            return "I'm sorry, there seems to be missing information. Let's start the booking process again.", None, None, session_data
        
        # Clear confirmation state and process booking directly
        session_data.pop('awaiting_confirmation', None)
        
        # Convert pending_booking to proper intent format
        booking_intent = {
            'action': 'book',
            'date': pending_booking['date'],
            'time': pending_booking['time'],
            'party_size': pending_booking['party_size'],
            'name': pending_booking['name'],
            'email': pending_booking['email'],
            'phone': pending_booking.get('phone', '')
        }
        
        # Process booking with enforced checks
        response_text, booking_data, availability_data, updated_session = await self.process_booking_action(booking_intent, session_data)
        
        # Clear pending booking after processing
        updated_session.pop('pending_booking', None)
        
        return response_text, booking_data, availability_data, updated_session
    
    async def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    async def extract_booking_intent(self, message: str) -> Optional[dict]:
        """Extract booking intent and details from user message"""
        intent: Dict[str, Any] = {}
        
        print(f"Extracting intent from message: {message}")
        
        # Check for booking intent keywords
        booking_keywords = ['book', 'reserve', 'reservation', 'table', 'availability', 'available', 'modify', 'change', 'update', 'cancel', 'check', 'status', 'details', 'what time']
        found_keywords = [kw for kw in booking_keywords if kw in message.lower()]
        print(f"Found booking keywords: {found_keywords}")
        
        if any(keyword in message.lower() for keyword in booking_keywords):
            lower = message.lower()
            if 'modify' in lower or 'change' in lower or 'update' in lower:
                intent['action'] = 'modify'
            elif 'cancel' in lower:
                intent['action'] = 'cancel'
            elif ('check' in lower or 'status' in lower or 'details' in lower or 'what time' in lower):
                intent['action'] = 'get_booking'
            elif 'availability' in lower or 'available' in lower:
                intent['action'] = 'check_availability'
            else:
                intent['action'] = 'book'
        
        # Extract date information
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
            r'(today|tomorrow|next \w+)',       # today, tomorrow, next friday
            r'(\w+ \d{1,2})',                   # March 15
        ]
        for pattern in date_patterns:
            match = re.search(pattern, message.lower())
            if match:
                intent['date'] = match.group(1)
                break
        
        # Extract time information
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:am|pm)?)',   # 7:30pm, 19:30
            r'(\d{1,2}\s*(?:am|pm))',          # 7pm, 7 pm
            r'at (\d{1,2})',                   # at 7
        ]
        for pattern in time_patterns:
            match = re.search(pattern, message.lower())
            if match:
                intent['time'] = match.group(1)
                break
        
        # Extract party size
        party_patterns = [
            r'(\d+)\s*people',
            r'(\d+)\s*guests',
            r'party of (\d+)',
            r'for (\d+)',
            r'table for (\d+)',
        ]
        for pattern in party_patterns:
            match = re.search(pattern, message.lower())
            if match:
                intent['party_size'] = int(match.group(1))
                break
        
        # Extract customer information
        ref_match = re.search(r'\b([A-Z0-9]{7})\b', message)
        if ref_match:
            intent['reference'] = ref_match.group(1)

        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
        if email_match:
            intent['email'] = email_match.group(0)
        
        phone_match = re.search(r'[\+]?[\d\s\-\(\)]{10,}', message)
        if phone_match:
            intent['phone'] = phone_match.group(0)
        
        # Extract name - more flexible patterns with better validation
        name_patterns = [
            r'name is ([A-Za-z\s]+)',
            r'i\'m ([A-Za-z\s]+)',
            r'my name\'s ([A-Za-z\s]+)',
            r'name ([A-Za-z]+\s+[A-Za-z]+)',  # Require at least first + last name
            r'\bname\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # Capitalized names after "name"
        ]
        
        # Also try to find capitalized names in the message
        capitalized_name_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
        cap_matches = re.findall(capitalized_name_pattern, message)
        
        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                potential_name = match.group(1).strip().title()
                # Validate it looks like a real name
                excluded_words = ['book', 'table', 'people', 'tomorrow', 'today', 'reservation', 'restaurant', 'hungry', 'unicorn']
                if (len(potential_name.split()) >= 2 and 
                    not any(word in potential_name.lower() for word in excluded_words) and
                    all(part.isalpha() for part in potential_name.split())):
                    intent['name'] = potential_name
                    print(f"Extracted name from pattern: {potential_name}")
                    break
        
        # If no name found from patterns, try capitalized names
        if 'name' not in intent and cap_matches:
            for cap_name in cap_matches:
                excluded_words = ['book', 'table', 'people', 'tomorrow', 'today', 'reservation', 'restaurant', 'hungry', 'unicorn']
                if (not any(word in cap_name.lower() for word in excluded_words) and
                    all(part.isalpha() for part in cap_name.split())):
                    intent['name'] = cap_name
                    print(f"Extracted name from capitalized text: {cap_name}")
                    break
        
        if intent:
            print(f"Extracted intent: {intent}")
        else:
            print("No intent extracted")
            
        return intent if intent else None
    
    async def process_booking_action(self, intent: dict, session_data: dict) -> Tuple[str, Optional[dict], Optional[dict], dict]:
        """Process booking actions and return response with booking/availability data"""
        try:
            if intent.get('action') == 'check_availability':
                if intent.get('date') and intent.get('party_size'):
                    normalized_date = self.normalize_date_text(intent['date'])
                    if not normalized_date:
                        return "Please provide a valid date.", None, None, session_data
                    
                    availability_result = await booking_client.check_availability(normalized_date, intent['party_size'])
                    
                    if 'error' not in availability_result:
                        availability_data = {
                            'date': normalized_date,
                            'party_size': intent['party_size'],
                            'slots': availability_result.get('available_slots', [])
                        }
                        session_data.setdefault('booking', {})
                        session_data['booking'].update({
                            'last_checked_date': normalized_date,
                            'last_checked_party_size': intent['party_size'],
                            'available_slots': availability_result.get('available_slots', [])
                        })
                        return f"Great! I found availability for {intent['party_size']} people on {normalized_date}.", None, availability_data, session_data
                    else:
                        return f"I'm sorry, I couldn't check availability right now. {availability_result['error']}", None, None, session_data
                else:
                    return "To check availability, I need both the date and party size.", None, None, session_data
            
            elif intent.get('action') == 'book':
                required_fields = ['date', 'time', 'party_size', 'name', 'email']
                missing_fields = [field for field in required_fields if not intent.get(field)]
                
                if missing_fields:
                    session_data.setdefault('booking', {})
                    session_data['booking'].update(intent)
                    return f"I'd be happy to help you make a reservation! I still need: {', '.join(missing_fields)}. Could you please provide this information?", None, None, session_data
                
                # Normalize date first
                normalized_date = self.normalize_date_text(intent['date'])
                if not normalized_date:
                    return "Please provide a valid date (e.g., 'tomorrow', 'January 15', '2025-01-15').", None, None, session_data
                
                # ENFORCE AVAILABILITY CHECK - Must pass before booking
                print(f"Checking availability for {normalized_date} with party size {intent['party_size']}")
                availability_check = await booking_client.check_availability(normalized_date, intent['party_size'])
                print(f"Availability check result: {availability_check}")
                
                if 'error' in availability_check:
                    return f"I'm sorry, I couldn't check availability right now: {availability_check['error']}. Please try again later.", None, None, session_data
                
                # Parse the requested time to check against available slots
                requested_time_24h = self._parse_time_to_24h(intent['time'])
                print(f"Requested time in 24h format: {requested_time_24h}")
                
                available_slots = availability_check.get('available_slots', [])
                if not available_slots:
                    return f"I'm sorry, there are no available slots for {intent['party_size']} people on {normalized_date}. Would you like to try a different date?", None, None, session_data
                
                # Check if the requested time slot is available
                matching_slot = None
                for slot in available_slots:
                    slot_time = slot.get('time', '')
                    if slot.get('available', False):
                        # Compare times (allow some flexibility - within 30 minutes)
                        if self._times_match(requested_time_24h, slot_time):
                            matching_slot = slot
                            break
                
                if not matching_slot:
                    # Show available alternatives
                    available_times = [slot['time'][:5] for slot in available_slots if slot.get('available', False)]
                    return f"I'm sorry, {intent['time']} is not available on {normalized_date} for {intent['party_size']} people. However, I have these times available: {', '.join(available_times)}. Would you like to book one of these instead?", None, None, session_data
                
                # Availability confirmed - proceed with booking
                customer_info = {
                    'name': intent['name'],
                    'email': intent['email'],
                    'phone': intent.get('phone', ''),
                    'special_requests': intent.get('special_requests', '')
                }
                
                print(f"Creating booking with: date={normalized_date}, time={intent['time']}, party_size={intent['party_size']}, customer_info={customer_info}")
                
                booking_result = await booking_client.create_booking(
                    normalized_date, intent['time'], intent['party_size'], customer_info
                )
                
                print(f"Booking creation result: {booking_result}")
                
                # ENFORCE SUCCESSFUL BOOKING SAVE
                if 'error' not in booking_result:
                    booking_ref = booking_result.get('booking_reference')
                    
                    if booking_ref:
                        # BOOKING SUCCESSFULLY SAVED TO DATABASE
                        print(f"✅ BOOKING SAVED TO DATABASE: {booking_ref}")
                        
                        # Verify the booking was actually saved by fetching it back
                        verification = await booking_client.get_booking(booking_ref)
                        if 'error' in verification:
                            return f"Booking was created but verification failed. Reference: {booking_ref}. Please contact support if you have issues.", None, None, session_data
                        
                        # Booking confirmed and verified - create comprehensive response
                        booking_data = {
                            'date': normalized_date,
                            'time': intent['time'],
                            'party': intent['party_size'],
                            'reference': booking_ref,
                            'status': booking_result.get('status', 'confirmed'),
                            'restaurant': booking_result.get('restaurant', 'TheHungryUnicorn'),
                            'visit_date': booking_result.get('visit_date'),
                            'visit_time': booking_result.get('visit_time'),
                            'customer': booking_result.get('customer', {}),
                            'verified': True
                        }
                        
                        # Persist in session for future reference
                        session_data.setdefault('booking', {})
                        session_data['booking'].update({
                            'reference': booking_ref,
                            'date': normalized_date,
                            'time': intent['time'],
                            'party_size': intent['party_size'],
                            'customer_name': intent['name'],
                            'customer_email': intent['email'],
                            'status': 'confirmed'
                        })
                        
                        customer_name = intent.get('name', 'Guest')
                        success_message = f"🎉 **RESERVATION CONFIRMED & SAVED!**\n\n"
                        success_message += f"📅 **Booking Details:**\n"
                        success_message += f"🍽️ Restaurant: TheHungryUnicorn\n"
                        success_message += f"📆 Date: {normalized_date}\n"
                        success_message += f"🕐 Time: {intent['time']}\n"
                        success_message += f"👥 Party Size: {intent['party_size']} people\n"
                        success_message += f"👤 Customer: {customer_name}\n"
                        success_message += f"📧 Email: {intent['email']}\n"
                        if intent.get('phone'):
                            success_message += f"📞 Phone: {intent['phone']}\n"
                        success_message += f"🎫 **Reference: {booking_ref}**\n\n"
                        success_message += f"✅ Your booking has been saved to our system and confirmed!\n"
                        success_message += f"💾 You can use reference **{booking_ref}** to check, modify, or cancel your reservation.\n"
                        success_message += f"📱 Please save this reference number for your records."
                        
                        return success_message, booking_data, None, session_data
                    else:
                        # This is a critical error - booking API didn't return reference
                        return f"❌ CRITICAL ERROR: Booking was processed but no reference number was returned. This should not happen. Please contact support immediately.", None, None, session_data
                else:
                    # Booking failed - show specific error
                    error_msg = booking_result.get('error', 'Unknown error')
                    return f"❌ **Booking Failed**\n\nI'm sorry, I couldn't complete your reservation due to: {error_msg}\n\nPlease try again or contact support if the problem persists.", None, None, session_data
            
            elif intent.get('action') == 'get_booking':
                reference = intent.get('reference') or session_data.get('booking', {}).get('reference')
                if not reference:
                    return "Please share your 7-character booking reference so I can fetch the details.", None, None, session_data
                
                result = await booking_client.get_booking(reference)
                if 'error' in result:
                    return f"I couldn't retrieve your booking: {result['error']}", None, None, session_data
                
                session_data.setdefault('booking', {})
                session_data['booking'].update({'reference': reference})
                
                booking_data = {
                    'date': str(result.get('visit_date')),
                    'time': str(result.get('visit_time')),
                    'party': result.get('party_size'),
                    'reference': reference,
                    'status': result.get('status', 'confirmed'),
                    'restaurant': result.get('restaurant', 'TheHungryUnicorn'),
                    'special_requests': result.get('special_requests', ''),
                    'customer': result.get('customer', {}),
                    'created_at': result.get('created_at'),
                    'updated_at': result.get('updated_at')
                }
                
                # Format response message
                customer = result.get('customer', {})
                customer_name = f"{customer.get('first_name', '')} {customer.get('surname', '')}".strip()
                special_requests = result.get('special_requests', '')
                
                message = f"📋 **Booking Details for {reference}**\n\n"
                message += f"🍽️ Restaurant: {result.get('restaurant', 'TheHungryUnicorn')}\n"
                message += f"📅 Date: {result.get('visit_date')}\n"
                message += f"🕐 Time: {result.get('visit_time')}\n"
                message += f"👥 Party Size: {result.get('party_size')}\n"
                if customer_name:
                    message += f"👤 Customer: {customer_name}\n"
                if customer.get('email'):
                    message += f"📧 Email: {customer.get('email')}\n"
                if special_requests:
                    message += f"💬 Special Requests: {special_requests}\n"
                message += f"✅ Status: {result.get('status', 'confirmed').title()}"
                
                return message, booking_data, None, session_data

            elif intent.get('action') == 'cancel':
                reference = intent.get('reference') or session_data.get('booking', {}).get('reference')
                if not reference:
                    return "To cancel, please share your 7-character booking reference.", None, None, session_data
                
                cancel_result = await booking_client.cancel_booking(reference, microsite_name=RESTAURANT_NAME)
                if 'error' in cancel_result:
                    return f"I couldn't cancel your booking: {cancel_result['error']}", None, None, session_data
                
                session_data.setdefault('booking', {})
                session_data['booking'].update({'reference': reference, 'status': 'cancelled'})
                
                cancellation_reason = cancel_result.get('cancellation_reason', 'Customer Request')
                message = f"❌ **Booking Cancelled**\n\n"
                message += f"Reference: {reference}\n"
                message += f"Reason: {cancellation_reason}\n"
                message += f"Status: Cancelled\n\n"
                message += "Your booking has been successfully cancelled. If you need to make a new reservation, I'm here to help!"
                
                return message, None, None, session_data

            elif intent.get('action') == 'modify':
                reference = intent.get('reference') or session_data.get('booking', {}).get('reference')
                if not reference:
                    return "Please provide your 7-character booking reference to modify your reservation.", None, None, session_data

                new_date = intent.get('date')
                new_time = intent.get('time')
                new_party = intent.get('party_size')
                if not any([new_date, new_time, new_party]):
                    return "What would you like to change? You can update the date, time, or party size.", None, None, session_data

                # Get current booking details for context
                current_booking = await booking_client.get_booking(reference)
                if 'error' in current_booking:
                    return f"I couldn't retrieve your current booking: {current_booking['error']}", None, None, session_data

                # Determine final values after modification
                final_date = self.normalize_date_text(new_date) if new_date else current_booking.get('visit_date')
                final_party_size = new_party if new_party else current_booking.get('party_size')
                final_time = new_time if new_time else current_booking.get('visit_time')

                # ENFORCE AVAILABILITY CHECK for modifications
                if new_date or new_party:  # Check availability if date or party size changes
                    print(f"Checking availability for modification: {final_date}, party size: {final_party_size}")
                    availability_check = await booking_client.check_availability(final_date, final_party_size)
                    
                    if 'error' in availability_check:
                        return f"I couldn't check availability for your modification: {availability_check['error']}", None, None, session_data
                    
                    available_slots = availability_check.get('available_slots', [])
                    if not available_slots:
                        return f"I'm sorry, there are no available slots for {final_party_size} people on {final_date}. Your original booking remains unchanged.", None, None, session_data
                    
                    # If time is also changing, check if new time is available
                    if new_time:
                        requested_time_24h = self._parse_time_to_24h(new_time)
                        matching_slot = None
                        for slot in available_slots:
                            if slot.get('available', False) and self._times_match(requested_time_24h, slot.get('time', '')):
                                matching_slot = slot
                                break
                        
                        if not matching_slot:
                            available_times = [slot['time'][:5] for slot in available_slots if slot.get('available', False)]
                            return f"I'm sorry, {new_time} is not available on {final_date} for {final_party_size} people. Available times: {', '.join(available_times)}. Your original booking remains unchanged.", None, None, session_data

                # Availability confirmed - proceed with update
                update_result = await booking_client.update_booking(
                    reference, 
                    date=self.normalize_date_text(new_date) if new_date else None, 
                    time=new_time, 
                    party_size=new_party
                )
                
                if 'error' in update_result:
                    return f"I couldn't update your booking: {update_result['error']}", None, None, session_data

                # Update session data
                session_data.setdefault('booking', {})
                if new_date:
                    session_data['booking']['date'] = self.normalize_date_text(new_date)
                if new_time:
                    session_data['booking']['time'] = new_time
                if new_party:
                    session_data['booking']['party_size'] = new_party

                # Verify the update by fetching the booking again
                verification = await booking_client.get_booking(reference)
                if 'error' not in verification:
                    success_message = f"✅ **Booking Updated Successfully!**\n\n"
                    success_message += f"🎫 Reference: {reference}\n"
                    success_message += f"📆 Date: {verification.get('visit_date')}\n"
                    success_message += f"🕐 Time: {verification.get('visit_time')}\n"
                    success_message += f"👥 Party Size: {verification.get('party_size')}\n"
                    success_message += f"💾 Your changes have been saved to our system."
                    return success_message, None, None, session_data
                else:
                    return "Your booking has been updated successfully.", None, None, session_data

            return "I understand you're interested in booking. How can I help you with your reservation?", None, None, session_data
            
        except Exception as e:
            return f"I apologize, but I encountered an issue processing your request: {str(e)}", None, None, session_data
    
    async def generate_response(self, message: str, conversation_history: list = None, session_data: dict = None) -> Tuple[str, Optional[dict], Optional[dict], dict]:
        """Generate AI response using hybrid AI + direct processing approach"""
        session_data = session_data or {}
        
        print(f"🔍 GENERATE_RESPONSE called with message: '{message}'")
        print(f"🔍 Message contains DIRECTBOOK: {'DIRECTBOOK' in message.upper()}")
        
        try:
            # FORCE DIRECT MODE: Special keyword to bypass AI completely
            if "DIRECTBOOK" in message.upper():
                print("🔥 FORCE DIRECT MODE TRIGGERED")
                # Extract booking details and process directly
                booking_intent = await self.extract_booking_intent(message)
                if booking_intent:
                    print(f"🎯 Direct mode intent: {booking_intent}")
                    return await self.process_booking_action(booking_intent, session_data)
                else:
                    return "Direct booking mode activated, but I couldn't extract booking details. Please include: date, time, party size, name, email", None, None, session_data
            
            # Check for DIRECT booking confirmations first (bypass AI)
            if self._is_booking_confirmation(message, session_data):
                print("🔄 Handling booking confirmation")
                return await self._handle_booking_confirmation(session_data)
            
            # Check for DIRECT booking commands (bypass AI)
            if self._is_direct_booking_command(message):
                print("📋 Direct booking command detected")
                booking_intent = await self.extract_booking_intent(message)
                if booking_intent:
                    merged_intent = {**session_data.get('booking', {}), **booking_intent}
                    session_data['booking'] = merged_intent
                    return await self.process_booking_action(merged_intent, session_data)
            
            # Check if we have PENDING booking data that needs confirmation
            pending_booking = session_data.get('pending_booking')
            if pending_booking and self._has_all_booking_details(pending_booking):
                # We have all details - ask for final confirmation
                confirmation_message = self._generate_confirmation_message(pending_booking)
                session_data['awaiting_confirmation'] = True
                return confirmation_message, None, None, session_data
            
            # Use AI to understand intent and gather information
            booking_intent = await self.extract_booking_intent(message)
            
            if booking_intent:
                print(f"AI detected booking intent: {booking_intent}")
                # Merge with any existing pending booking
                merged_intent = {**session_data.get('pending_booking', {}), **booking_intent}
                session_data['pending_booking'] = merged_intent
                
                # Check if we now have all required details
                if self._has_all_booking_details(merged_intent):
                    # Switch to direct confirmation mode
                    confirmation_message = self._generate_confirmation_message(merged_intent)
                    session_data['awaiting_confirmation'] = True
                    return confirmation_message, None, None, session_data
                else:
                    # Still missing info - let AI handle the conversation
                    enhanced_message = f"Customer wants to book: {message}\nCurrent booking info: {merged_intent}"
            else:
                enhanced_message = message
            
            # Prepare conversation context for Ollama
            messages = []
            
            # Concise, gentle system prompt
            system_prompt = """You are TableBooker, the gentle and concise booking assistant for TheHungryUnicorn.

Capabilities:
- Check availability for specific dates and times
- Make new restaurant reservations
- Check existing booking details using references
- Modify reservations (change date/time/party size)
- Cancel reservations completely

Principles:
- Be brief, warm, and helpful. No repetition. Prefer short bullets.
- Minimize turns by batching requests for missing info into one checklist.
- Confirm availability before booking; suggest 2–3 nearby times if needed.
- Handle natural language dates/times (today, tomorrow, next Friday, 7pm, etc.)

Restaurant Info:
- TheHungryUnicorn: Fine dining, modern European cuisine
- Hours: Tuesday-Sunday 5:00 PM - 11:00 PM, Closed Mondays

Booking data:
- New booking requires: Date, Time, Party size, Name, Email. Phone is optional.
- Check/Modify/Cancel requires: 7-character booking reference
- Accept any natural date/time format - system will normalize it

When details are missing, reply once with only the missing items. Examples:
"Happy to help! Could you share in one message:
- Date (any format is fine):
- Time (any format is fine):
- Party size:
- Name:
- Email:
- Phone (optional):"

For modifications: "What would you like to change? (date, time, or party size)"
For cancellations: "Please provide your booking reference to cancel."

Keep tone kind and professional, but prioritize clarity and brevity."""

            messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history (last 4 messages for better context)
            if conversation_history:
                for msg in conversation_history[-4:]:
                    messages.append(msg)
            
            # Add current enhanced message
            messages.append({"role": "user", "content": enhanced_message})
            
            # Call Ollama API
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["message"]["content"]
                return ai_response, None, None, session_data
            else:
                return "I'm having trouble connecting to my AI system. How can I help you with restaurant bookings?", None, None, session_data
                
        except Exception as e:
            print(f"Ollama error: {e}")
            return "I'm experiencing some technical difficulties, but I'm still here to help with your restaurant booking needs!", None, None, session_data

# Initialize AI
ai = OllamaAI()

@app.get("/")
async def root():
    """API information"""
    ollama_status = await ai.is_available()
    return {
        "service": "TableBooker AI Agent API (Ollama)",
        "version": "1.0.0",
        "status": "running",
        "ai_provider": "Ollama",
        "model": MODEL_NAME,
        "ollama_available": ollama_status,
        "features": ["AI conversations", "Restaurant booking", "Natural language understanding"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        ollama_status = await ai.is_available()
        health_status = "healthy" if ollama_status else "degraded"
        
        response_data = {
            "status": health_status,
            "service": "TableBooker AI Agent API (Ollama)",
            "ai_provider": "Ollama",
            "model": MODEL_NAME,
            "ollama_available": ollama_status
        }
        
        return response_data
    except Exception as e:
        return {
            "status": "error",
            "service": "TableBooker AI Agent API (Ollama)",
            "ai_provider": "Ollama",
            "model": MODEL_NAME,
            "ollama_available": False,
            "error": str(e)
        }

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with the Ollama-powered AI agent
    """
    try:
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Initialize session if new
        if session_id not in sessions:
            sessions[session_id] = {
                "created_at": datetime.now(),
                "conversation_history": [],
                "current_restaurant": "TheHungryUnicorn",
                "session_data": {}
            }
        
        session = sessions[session_id]
        
        # Generate AI response with booking intelligence
        response_message, booking_data, availability_data, updated_session = await ai.generate_response(
            request.message,
            session["conversation_history"],
            session["session_data"]
        )

        # Persist updated session data
        session["session_data"] = updated_session
        
        # Update conversation history
        session["conversation_history"].append({"role": "user", "content": request.message})
        session["conversation_history"].append({"role": "assistant", "content": response_message})
        
        # Keep only last 10 messages to prevent memory issues
        if len(session["conversation_history"]) > 10:
            session["conversation_history"] = session["conversation_history"][-10:]
        
        # Generate contextual suggestions
        suggestions = generate_suggestions(request.message, response_message, booking_data, availability_data)
        
        # Create response
        response = ChatResponse(
            message=response_message,
            session_id=session_id,
            suggestions=suggestions,
            conversation_state={
                "current_restaurant": session["current_restaurant"],
                "message_count": len(session["conversation_history"]) // 2,
                "has_booking_data": booking_data is not None,
                "has_availability_data": availability_data is not None
            },
            booking_data=booking_data,
            availability_data=availability_data
        )
        
        print(f"🤖 Ollama Chat - User: {request.message}")
        print(f"🤖 Ollama Response: {response_message[:100]}...")
        
        return response
        
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

def generate_suggestions(user_message: str, ai_response: str, booking_data: dict = None, availability_data: dict = None) -> list:
    """Generate contextual suggestions based on the conversation"""
    user_lower = user_message.lower()
    ai_lower = ai_response.lower()
    
    suggestions = []
    
    # Priority suggestions based on data presence
    if booking_data:
        status = booking_data.get('status', 'confirmed')
        if status == 'cancelled':
            suggestions = ["Make new reservation", "Check availability", "Restaurant info"]
        else:
            suggestions = ["Modify reservation", "Cancel reservation", "Check booking status"]
    elif availability_data:
        suggestions = ["Book this time", "Check different times", "Try different party size"]
    else:
        # Context-aware suggestions based on user stories
        if any(word in user_lower for word in ['hello', 'hi', 'start']):
            suggestions = ["Check availability this weekend", "Make a reservation", "Check my booking"]
        elif any(word in user_lower for word in ['restaurant', 'info', 'about']):
            suggestions = ["Check availability", "Make booking", "Restaurant hours"]
        elif any(word in user_lower for word in ['availability', 'check', 'free', 'available']):
            suggestions = ["Book available time", "Try different date", "Change party size"]
        elif any(word in user_lower for word in ['book', 'reserve', 'table']):
            suggestions = ["Check availability first", "Provide booking details", "Restaurant info"]
        elif any(word in user_lower for word in ['modify', 'change', 'update']):
            suggestions = ["Change date/time", "Change party size", "Cancel booking"]
        elif any(word in user_lower for word in ['cancel']):
            suggestions = ["Confirm cancellation", "Make new booking", "Check availability"]
        elif any(word in ai_lower for word in ['booking', 'reservation', 'table']):
            suggestions = ["Make reservation", "Check availability", "Check my booking"]
        elif any(word in ai_lower for word in ['need', 'require', 'missing']):
            suggestions = ["Provide missing info", "Start over", "Get help"]
        else:
            suggestions = ["Check availability", "Make reservation", "Check my booking"]
    
    return suggestions[:3]  # Limit to 3 suggestions

@app.get("/ollama/status")
async def ollama_status():
    """Check Ollama status"""
    available = await ai.is_available()
    return {
        "ollama_available": available,
        "base_url": OLLAMA_BASE_URL,
        "model": MODEL_NAME,
        "status": "connected" if available else "disconnected"
    }

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return {
        "session_id": session_id,
        "created_at": session["created_at"],
        "message_count": len(session["conversation_history"]) // 2,
        "current_restaurant": session["current_restaurant"],
        "status": "active"
    }

@app.post("/test-intent")
async def test_intent_extraction(request: dict):
    """Test endpoint to debug intent extraction"""
    message = request.get("message", "")
    intent = await ai.extract_booking_intent(message)
    return {
        "message": message,
        "extracted_intent": intent,
        "has_intent": intent is not None
    }

@app.post("/direct-booking")
async def direct_booking_test(request: dict):
    """Direct booking test to bypass intent extraction"""
    # Create a mock intent for testing
    mock_intent = {
        'action': 'book',
        'date': 'tomorrow',
        'time': '7pm',
        'party_size': 4,
        'name': 'John Smith',
        'email': 'john@test.com'
    }
    
    session_data = {}
    response_text, booking_data, availability_data, updated_session = await ai.process_booking_action(mock_intent, session_data)
    
    return {
        "response": response_text,
        "booking_data": booking_data,
        "availability_data": availability_data,
        "session_data": updated_session
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🦙 Starting TableBooker AI Agent with Ollama")
    print("📡 Server will run on http://localhost:8000")
    print("🤖 AI Provider: Ollama (llama3.1:8b)")
    print("🔗 Ollama URL: http://localhost:11434")
    print("=" * 50)
    
    uvicorn.run(
        "main_clean:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
