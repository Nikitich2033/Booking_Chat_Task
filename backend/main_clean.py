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
            
            # Parse date and time strings to proper format
            visit_date = datetime.strptime(date, '%Y-%m-%d').date()
            
            # Parse time - handle various formats
            if ':' in time:
                # Handle "7:00pm" or "19:00" format
                time_str = time.lower().replace('pm', '').replace('am', '').strip()
                if 'pm' in time.lower() and not time_str.startswith(('12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23')):
                    hour, minute = time_str.split(':')
                    hour = int(hour) + 12 if int(hour) != 12 else 12
                    visit_time = datetime.strptime(f"{hour}:{minute}", '%H:%M').time()
                else:
                    visit_time = datetime.strptime(time_str, '%H:%M').time()
            else:
                # Handle "7pm" format
                time_str = time.lower().replace('pm', '').replace('am', '').strip()
                hour = int(time_str)
                if 'pm' in time.lower() and hour != 12:
                    hour += 12
                elif 'am' in time.lower() and hour == 12:
                    hour = 0
                visit_time = datetime.strptime(f"{hour}:00", '%H:%M').time()
            
            data = {
                "VisitDate": visit_date.isoformat(),
                "VisitTime": visit_time.isoformat(),
                "PartySize": party_size,
                "ChannelCode": "ONLINE"
            }
            
            # Add customer information with correct field names
            if customer_info.get("name"):
                name_parts = customer_info["name"].split(" ", 1)
                data["Customer[FirstName]"] = name_parts[0]
                if len(name_parts) > 1:
                    data["Customer[Surname]"] = name_parts[1]
            
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
                return response.json()
            else:
                return {"error": f"API error: {response.status_code} - {response.text}"}
                
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
                # Normalize to HH:MM:SS
                t = time.strip().lower()
                if ':' in t:
                    # handle 7:00pm / 19:00
                    pm = 'pm' in t
                    t = t.replace('am', '').replace('pm', '').strip()
                    hour, minute = t.split(':')
                    hour_i = int(hour)
                    if pm and hour_i != 12:
                        hour_i += 12
                    if not pm and 'am' not in time and len(hour) == 1 and hour_i < 7:
                        # best-effort: assume evening if ambiguous (skip)
                        pass
                    data["VisitTime"] = f"{hour_i:02d}:{int(minute):02d}:00"
                else:
                    # 7pm / 7
                    pm = 'pm' in t
                    t = t.replace('am', '').replace('pm', '').strip()
                    hour_i = int(t)
                    if pm and hour_i != 12:
                        hour_i += 12
                    if not pm and hour_i == 12:
                        hour_i = 0
                    data["VisitTime"] = f"{hour_i:02d}:00:00"

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
        
        # Check for booking intent keywords
        booking_keywords = ['book', 'reserve', 'reservation', 'table', 'availability', 'available', 'modify', 'change', 'update', 'cancel', 'check', 'status', 'details', 'what time']
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
        
        # Extract name
        name_patterns = [
            r'name is ([A-Za-z\s]+)',
            r'i\'m ([A-Za-z\s]+)',
            r'my name\'s ([A-Za-z\s]+)',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message.lower())
            if match:
                intent['name'] = match.group(1).strip().title()
                break
        
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
                    return f"I'd be happy to help you make a reservation! I still need: {', '.join(missing_fields)}.", None, None, session_data
                
                customer_info = {
                    'name': intent['name'],
                    'email': intent['email'],
                    'phone': intent.get('phone', ''),
                    'special_requests': intent.get('special_requests', '')
                }
                
                normalized_date = self.normalize_date_text(intent['date'])
                if not normalized_date:
                    return "Please provide a valid date.", None, None, session_data
                
                # Check availability first
                availability_check = await booking_client.check_availability(normalized_date, intent['party_size'])
                if 'available_slots' in availability_check:
                    slot_ok = any(s.get('time','').startswith(intent['time'][:2]) and s.get('available') for s in availability_check['available_slots'])
                    if not slot_ok:
                        return f"I couldn't verify availability for {normalized_date} at {intent['time']} for {intent['party_size']} people.", None, None, session_data
                
                booking_result = await booking_client.create_booking(
                    normalized_date, intent['time'], intent['party_size'], customer_info
                )
                
                if 'error' not in booking_result:
                    booking_data = {
                        'date': normalized_date,
                        'time': intent['time'],
                        'party': intent['party_size'],
                        'reference': booking_result.get('booking_reference'),
                        'status': booking_result.get('status', 'confirmed')
                    }
                    session_data.setdefault('booking', {})
                    session_data['booking'].update({
                        'reference': booking_result.get('booking_reference'),
                        'date': normalized_date,
                        'time': intent['time'],
                        'party_size': intent['party_size']
                    })
                    return f"Excellent! Your reservation has been confirmed. Reference: {booking_result.get('booking_reference')}", booking_data, None, session_data
                else:
                    return f"I'm sorry, I couldn't complete your booking. {booking_result['error']}", None, None, session_data
            
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
                    'status': result.get('status', 'confirmed')
                }
                return "Here are your booking details.", booking_data, None, session_data

            elif intent.get('action') == 'cancel':
                reference = intent.get('reference') or session_data.get('booking', {}).get('reference')
                if not reference:
                    return "To cancel, please share your 7-character booking reference.", None, None, session_data
                
                cancel_result = await booking_client.cancel_booking(reference, microsite_name=RESTAURANT_NAME)
                if 'error' in cancel_result:
                    return f"I couldn't cancel your booking: {cancel_result['error']}", None, None, session_data
                
                session_data.setdefault('booking', {})
                session_data['booking'].update({'reference': reference, 'status': 'cancelled'})
                
                return f"Your booking {reference} has been cancelled.", None, None, session_data

            elif intent.get('action') == 'modify':
                reference = intent.get('reference') or session_data.get('booking', {}).get('reference')
                if not reference:
                    return "Please provide your 7-character booking reference to modify your reservation.", None, None, session_data

                new_date = intent.get('date')
                new_time = intent.get('time')
                new_party = intent.get('party_size')
                if not any([new_date, new_time, new_party]):
                    return "What would you like to change? You can update the date, time, or party size.", None, None, session_data

                update_result = await booking_client.update_booking(reference, date=new_date, time=new_time, party_size=new_party)
                if 'error' in update_result:
                    return f"I couldn't update your booking: {update_result['error']}", None, None, session_data

                session_data.setdefault('booking', {})
                if new_date:
                    session_data['booking']['date'] = new_date
                if new_time:
                    session_data['booking']['time'] = new_time
                if new_party:
                    session_data['booking']['party_size'] = new_party

                return "Your booking has been updated successfully.", None, None, session_data

            return "I understand you're interested in booking. How can I help you with your reservation?", None, None, session_data
            
        except Exception as e:
            return f"I apologize, but I encountered an issue processing your request: {str(e)}", None, None, session_data
    
    async def generate_response(self, message: str, conversation_history: list = None, session_data: dict = None) -> Tuple[str, Optional[dict], Optional[dict], dict]:
        """Generate AI response using Ollama and booking intelligence"""
        session_data = session_data or {}
        
        try:
            # First, check for booking intent and handle it directly
            booking_intent = await self.extract_booking_intent(message)
            
            if booking_intent:
                # Merge with session data for progressive booking
                merged_intent = {**session_data.get('booking', {}), **booking_intent}
                session_data['booking'] = merged_intent
                
                response_text, booking_data, availability_data, session_data = await self.process_booking_action(merged_intent, session_data)
                
                # If we have booking/availability data, return it directly without Ollama
                if booking_data or availability_data:
                    return response_text, booking_data, availability_data, session_data
                
                # For partial booking info, use Ollama with simplified context
                if merged_intent:
                    enhanced_message = f"Customer message: {message}\nBooking context: Date={merged_intent.get('date','?')}, Time={merged_intent.get('time','?')}, Party={merged_intent.get('party_size','?')}"
                else:
                    enhanced_message = message
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
