"""
TableBooker AI Agent Backend with LangGraph Framework
Multi-tier AI system: OpenAI -> Ollama -> Simple Mode
"""
import asyncio
import uuid
import httpx
import re
import json
import os
from typing import Dict, Any, Optional, Tuple, TypedDict, Annotated
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Date, Time, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama import OllamaLLM

# Models
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
    ai_mode: str = "unknown"

# Agent State for LangGraph - Following official patterns
class AgentState(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
    user_input: str
    session_data: Dict[str, Any]
    booking_intent: Optional[Dict[str, Any]]
    response: str
    booking_data: Optional[Dict[str, Any]]
    availability_data: Optional[Dict[str, Any]]
    error: Optional[str]

# Removed AI mode enum - using Ollama only

# Create FastAPI app
app = FastAPI(
    title="TableBooker AI Agent API (LangGraph + Ollama)",
    description="Restaurant booking with LangGraph and Ollama LLM",
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

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.1:8b"
BOOKING_API_BASE_URL = "http://localhost:8547"
RESTAURANT_NAME = "TheHungryUnicorn"
BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFwcGVsbGErYXBpQHJlc2RpYXJ5LmNvbSIsIm5iZiI6MTc1NDQzMDgwNSwiZXhwIjoxNzU0NTE3MjA1LCJpYXQiOjE3NTQ0MzA4MDUsImlzcyI6IlNlbGYiLCJhdWQiOiJodHRwczovL2FwaS5yZXNkaWFyeS5jb20ifQ.g3yLsufdk8Fn2094SB3J3XW-KdBc0DY9a2Jiu_56ud8"

# Database Configuration
DATABASE_URL = "sqlite:///../../Restaurant-Booking-Mock-API-Server/restaurant_booking.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    microsite_name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, let the caller handle it

# Simple in-memory storage
sessions = {}

# Booking API Client
class BookingAPIClient:
    """Client for interacting with the restaurant booking API"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.base_url = BOOKING_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Restaurant metadata (static info not in database)
        self._restaurant_metadata = {
            "TheHungryUnicorn": {
                "description": "Upscale modern European cuisine",
                "cuisine": "European",
                "price_range": "$$$$"
            },
            "PizzaPalace": {
                "description": "Authentic Italian pizzas and pasta",
                "cuisine": "Italian",
                "price_range": "$$$"
            },
            "SushiZen": {
                "description": "Fresh sushi and Japanese cuisine",
                "cuisine": "Japanese", 
                "price_range": "$$$$"
            },
            "CafeBistro": {
                "description": "Casual French bistro with daily specials",
                "cuisine": "French",
                "price_range": "$$"
            }
        }
    
    def get_available_restaurants(self) -> dict:
        """Get list of available restaurants from database"""
        db = get_db()
        try:
            restaurants = db.query(Restaurant).all()
            available_restaurants = {}
            
            for restaurant in restaurants:
                microsite_name = restaurant.microsite_name
                metadata = self._restaurant_metadata.get(microsite_name, {})
                
                available_restaurants[microsite_name] = {
                    "name": restaurant.name,
                    "description": metadata.get("description", "Restaurant"),
                    "cuisine": metadata.get("cuisine", "International"),
                    "price_range": metadata.get("price_range", "$$$")
                }
            
            return available_restaurants
        finally:
            db.close()
    
    async def get_restaurants_with_availability(self, date: str, party_size: int) -> dict:
        """Get only restaurants that have availability for the given date and party size"""
        all_restaurants = self.get_available_restaurants()
        available_restaurants = {}
        
        for restaurant_id, restaurant_info in all_restaurants.items():
            try:
                availability = await self.check_availability(date, party_size, restaurant_id)
                if 'error' not in availability:
                    available_slots = availability.get('available_slots', [])
                    # Only include restaurants that have at least one available time slot
                    available_times = [slot for slot in available_slots if slot.get('available', False)]
                    if available_times:
                        restaurant_info['available_times'] = available_times
                        restaurant_info['total_available_slots'] = len(available_times)
                        available_restaurants[restaurant_id] = restaurant_info
            except Exception as e:
                print(f"Error checking availability for {restaurant_id}: {e}")
                continue
                
        return available_restaurants
    
    def get_restaurant_info(self, restaurant_id: str) -> dict:
        """Get information about a specific restaurant from database"""
        db = get_db()
        try:
            restaurant = db.query(Restaurant).filter(Restaurant.microsite_name == restaurant_id).first()
            if restaurant:
                metadata = self._restaurant_metadata.get(restaurant_id, {})
                return {
                    "name": restaurant.name,
                    "description": metadata.get("description", "Restaurant"),
                    "cuisine": metadata.get("cuisine", "International"),
                    "price_range": metadata.get("price_range", "$$$")
                }
            return {}
        finally:
            db.close()
    
    def _normalize_time_to_hhmmss(self, time_str: str) -> str:
        """Convert various time formats to HH:MM:SS format required by API"""
        time_lower = time_str.lower().strip()
        
        if ':' in time_lower:
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
                    hour, minute = base_time.split(':')
                    return f"{int(hour):02d}:{int(minute):02d}:00"
            except ValueError:
                pass
        else:
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
        
        if time_str.count(':') == 2:
            return time_str
        else:
            return "19:00:00"  # Default to 7pm
    
    async def check_availability(self, date: str, party_size: int, restaurant_name: str = RESTAURANT_NAME) -> dict:
        """Check table availability for given date and party size"""
        try:
            data = {
                "VisitDate": date,
                "PartySize": str(party_size),
                "ChannelCode": "ONLINE"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/ConsumerApi/v1/Restaurant/{restaurant_name}/AvailabilitySearch",
                data=data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Failed to check availability: {str(e)}"}
    
    async def create_booking(self, date: str, time: str, party_size: int, customer_info: dict, restaurant_name: str = RESTAURANT_NAME) -> dict:
        """Create a new booking"""
        try:
            visit_date = datetime.strptime(date, '%Y-%m-%d').date()
            visit_time_str = self._normalize_time_to_hhmmss(time)
            
            data = {
                "VisitDate": visit_date.isoformat(),
                "VisitTime": visit_time_str,
                "PartySize": str(party_size),
                "ChannelCode": "ONLINE"
            }
            
            if customer_info.get("name"):
                name_parts = customer_info["name"].strip().split(" ", 1)
                data["Customer[FirstName]"] = name_parts[0]
                if len(name_parts) > 1:
                    data["Customer[Surname]"] = name_parts[1]
                else:
                    data["Customer[Surname]"] = ""
            
            if customer_info.get("email"):
                data["Customer[Email]"] = customer_info["email"]
            
            if customer_info.get("phone"):
                data["Customer[Mobile]"] = customer_info["phone"]
            
            if customer_info.get("special_requests"):
                data["SpecialRequests"] = customer_info["special_requests"]
            
            response = await self.client.post(
                f"{self.base_url}/api/ConsumerApi/v1/Restaurant/{restaurant_name}/BookingWithStripeToken",
                data=data,
                headers=self.headers
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Failed to create booking: {str(e)}"}
    
    async def get_booking(self, booking_reference: str, restaurant_name: str = RESTAURANT_NAME) -> dict:
        """Get booking details by reference"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/ConsumerApi/v1/Restaurant/{restaurant_name}/Booking/{booking_reference}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Failed to get booking: {str(e)}"}
    
    async def update_booking(self, booking_reference: str, updates: dict, restaurant_name: str = RESTAURANT_NAME) -> dict:
        """Update an existing booking"""
        try:
            data = {}
            
            # Map update fields to API format
            if "date" in updates:
                visit_date = datetime.strptime(updates["date"], '%Y-%m-%d').date()
                data["VisitDate"] = visit_date.isoformat()
            
            if "time" in updates:
                data["VisitTime"] = self._normalize_time_to_hhmmss(updates["time"])
            
            if "party_size" in updates:
                data["PartySize"] = str(updates["party_size"])
            
            if "special_requests" in updates:
                data["SpecialRequests"] = updates["special_requests"]
            
            response = await self.client.patch(
                f"{self.base_url}/api/ConsumerApi/v1/Restaurant/{restaurant_name}/Booking/{booking_reference}",
                data=data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Failed to update booking: {str(e)}"}
    
    async def cancel_booking(self, booking_reference: str, cancellation_reason_id: int = 1, restaurant_name: str = RESTAURANT_NAME) -> dict:
        """Cancel an existing booking"""
        try:
            data = {
                "micrositeName": restaurant_name,
                "bookingReference": booking_reference,
                "cancellationReasonId": str(cancellation_reason_id)
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/ConsumerApi/v1/Restaurant/{restaurant_name}/Booking/{booking_reference}/Cancel",
                data=data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code} - {response.text}"}
                
        except Exception as e:
            return {"error": f"Failed to cancel booking: {str(e)}"}

# Initialize booking API client
booking_client = BookingAPIClient()

# Intent Extraction Utilities
class IntentExtractor:
    """Extract booking intents from user messages"""
    
    @staticmethod
    def normalize_date_text(date_text: str) -> Optional[str]:
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
        
        # Month name + day (with or without year)
        for fmt in ("%B %d", "%b %d", "%B %d %Y", "%b %d %Y"):
            try:
                if "%Y" in fmt:
                    d = datetime.strptime(txt, fmt).date()
                else:
                    d = datetime.strptime(txt, fmt).replace(year=now.year).date()
                    if d < now.date():
                        d = d.replace(year=now.year + 1)
                return d.isoformat()
            except ValueError:
                pass
        
        return None
    
    @staticmethod
    async def extract_booking_intent(message: str) -> Optional[dict]:
        """Extract booking intent and details from user message"""
        intent: Dict[str, Any] = {}
        
        # Check for specific booking intent keywords with priority order
        lower = message.lower()
        
        # 1. Check for cancellation intent (highest priority)
        cancel_keywords = ['cancel', 'cancelled', 'delete', 'remove']
        if any(keyword in lower for keyword in cancel_keywords):
            intent['action'] = 'cancel_booking'
            print(f"❌ Intent: cancel_booking detected in message: {message}")
        
        # 2. Check for modification intent
        elif any(keyword in lower for keyword in ['change', 'modify', 'update', 'reschedule', 'move']):
            intent['action'] = 'update_booking'
            print(f"✏️ Intent: update_booking detected in message: {message}")
        
        # 3. Check for booking lookup intent
        elif any(keyword in lower for keyword in ['check my', 'my booking', 'my reservation', 'booking reference', 'find my']):
            intent['action'] = 'get_booking'
            print(f"🔍 Intent: get_booking detected in message: {message}")
        
        # 4. Check for availability intent
        elif 'availability' in lower or 'available' in lower:
            intent['action'] = 'check_availability'
            print(f"🔍 Intent: check_availability detected in message: {message}")
        
        # 5. Check for general booking keywords
        elif any(keyword in lower for keyword in ['book', 'reserve', 'reservation', 'table']):
            intent['action'] = 'book'
            print(f"📝 Intent: book detected in message: {message}")
        
        else:
            print(f"❌ No booking keywords found in message: {message}")
        
        # Extract date information
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(today|tomorrow|next \w+)',
            r'(\w+ \d{1,2})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, message.lower())
            if match:
                intent['date'] = match.group(1)
                break
        
        # Extract time information
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:am|pm)?)',
            r'(\d{1,2}\s*(?:am|pm))',
            r'at (\d{1,2})',
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
        
        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
        if email_match:
            intent['email'] = email_match.group(0)
        
        # Extract booking reference (alphanumeric codes with mixed case/numbers)
        booking_ref_patterns = [
            r'reference\s+([A-Z0-9]{6,8})',  # "reference ABC123"
            r'booking\s+reference\s+([A-Z0-9]{6,8})',  # "booking reference ABC123"
            r'ref\s+([A-Z0-9]{6,8})',  # "ref ABC123"
            r'#([A-Z0-9]{6,8})',  # "#ABC123"
            r'\b([A-Z0-9]*[0-9][A-Z0-9]*[A-Z][A-Z0-9]*|[A-Z0-9]*[A-Z][A-Z0-9]*[0-9][A-Z0-9]*)\b',  # Mixed letters/numbers pattern
        ]
        for pattern in booking_ref_patterns:
            match = re.search(pattern, message.upper())
            if match:
                ref = match.group(1)
                # Ensure it's not a common word and has mixed alphanumeric
                excluded_words = ['BOOKING', 'REFERENCE', 'TOMORROW', 'TONIGHT', 'CANCEL', 'CHANGE', 'UPDATE', 'MODIFY']
                if (ref not in excluded_words and 
                    len(ref) >= 6 and 
                    any(c.isdigit() for c in ref) and 
                    any(c.isalpha() for c in ref)):
                    intent['booking_reference'] = ref
                    print(f"Extracted booking reference: {ref}")
                    break
        
        # Extract restaurant preference
        # Get restaurant keywords from metadata
        restaurant_keywords = {}
        for restaurant_id, metadata in booking_client._restaurant_metadata.items():
            keywords = []
            
            # Add restaurant name parts
            name_parts = restaurant_id.lower().replace('the', '').split()
            keywords.extend(name_parts)
            
            # Add cuisine type
            if metadata.get('cuisine'):
                keywords.append(metadata['cuisine'].lower())
                
            # Add specific keywords based on restaurant
            if 'pizza' in restaurant_id.lower():
                keywords.extend(['pizza', 'pasta', 'italian'])
            elif 'sushi' in restaurant_id.lower():
                keywords.extend(['sushi', 'japanese'])
            elif 'unicorn' in restaurant_id.lower():
                keywords.extend(['unicorn', 'fine dining', 'european'])
            elif 'bistro' in restaurant_id.lower():
                keywords.extend(['bistro', 'cafe', 'french'])
                
            restaurant_keywords[restaurant_id] = keywords
        
        message_lower = message.lower()
        for restaurant_id, keywords in restaurant_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                intent['restaurant'] = restaurant_id
                break
        
        # Extract name - improved patterns
        name_patterns = [
            r'name is ([A-Za-z\s]+)',
            r'i\'m ([A-Za-z\s]+)',
            r'my name\'s ([A-Za-z\s]+)',
            r'people\s+([A-Z][a-z]+(?:\s+[A-Z])?)',  # "4 people Nik" or "4 people Nik L"
            r'for\s+\d+\s+people\s+([A-Z][a-z]+(?:\s+[A-Z])?)',  # "for 4 people Nik L"
            r'(\b[A-Z][a-z]+\s+[A-Z]\b)',  # "Nik L" - capitalized first and last initial
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                potential_name = match.group(1).strip()
                excluded_words = ['book', 'table', 'people', 'tomorrow', 'today', 'reservation', 'august', 'email']
                # Allow single names or two-word names
                if (len(potential_name.split()) >= 1 and 
                    not any(word.lower() in potential_name.lower() for word in excluded_words) and
                    potential_name.replace(' ', '').isalpha()):
                    intent['name'] = potential_name
                    print(f"Extracted name: {potential_name}")
                    break
        
        return intent if intent else None

# LangGraph Agent Framework
class BookingAgent:
    """LangGraph-based booking agent using Ollama"""
    
    def __init__(self):
        self.intent_extractor = IntentExtractor()
        
        # Initialize Ollama LLM
        try:
            self.ollama_llm = OllamaLLM(
                model=MODEL_NAME,
                base_url=OLLAMA_BASE_URL
            )
            print("✅ Ollama configured with langchain-ollama")
        except Exception as e:
            print(f"❌ Ollama initialization failed: {e}")
            raise Exception("Ollama is required for the booking agent to function")
        
        # Build the agent graph
        self.graph = self._build_agent_graph()
    
    def _build_agent_graph(self) -> StateGraph:
        """Build the LangGraph agent workflow following official patterns"""
        
        # Create a StateGraph with our defined state schema
        graph_builder = StateGraph(AgentState)
        
        # Add nodes (units of work) - simplified to only Ollama
        graph_builder.add_node("ollama_agent", self._ollama_agent_node)
        graph_builder.add_node("booking_processor", self._booking_processor_node)
        
        # Add entry point - start directly with Ollama
        graph_builder.add_edge(START, "ollama_agent")
        
        # Ollama agent routes to booking processor
        graph_builder.add_edge("ollama_agent", "booking_processor")
        
        # Add exit point - tell the graph where to finish execution
        graph_builder.add_edge("booking_processor", END)
        
        # Compile the graph into a runnable
        return graph_builder.compile()
    
    # Removed router, OpenAI, and simple agent nodes - using Ollama only
    
    async def _ollama_agent_node(self, state: AgentState) -> AgentState:
        """Ollama-powered agent node - follows LangGraph pattern"""
        print("🦙 Ollama Agent: Processing...")
        
        try:
            system_prompt = self._get_system_prompt()
            user_message = state["user_input"]
            
            # Build message list from current state with session context
            session_booking = state["session_data"].get("booking_info", {})
            context_info = ""
            if session_booking:
                context_info = f"\n\nCURRENT BOOKING INFORMATION:\n"
                for key, value in session_booking.items():
                    if value:
                        context_info += f"- {key.replace('_', ' ').title()}: {value}\n"
            
            # Add availability data if we have it
            if state.get('availability_data'):
                avail_data = state['availability_data']
                context_info += f"\n\nAVAILABILITY DATA:\n"
                
                if 'available_restaurants' in avail_data:
                    context_info += f"Available restaurants for {avail_data.get('date')} with {avail_data.get('party_size')} people:\n"
                    for rest_id, rest_info in avail_data['available_restaurants'].items():
                        times = [slot['time'] for slot in rest_info.get('available_times', [])]
                        context_info += f"- {rest_info['name']}: {', '.join(times[:3])}{'...' if len(times) > 3 else ''}\n"
                elif 'available_times' in avail_data:
                    restaurant_name = avail_data.get('restaurant', 'selected restaurant')
                    context_info += f"Available times at {restaurant_name} for {avail_data.get('date')} with {avail_data.get('party_size')} people:\n"
                    times = avail_data['available_times']
                    context_info += f"- {', '.join(times)}\n"
            
            enhanced_prompt = system_prompt + context_info
            messages = [SystemMessage(content=enhanced_prompt)]
            # Add existing messages from state if any  
            if state.get("messages"):
                messages.extend(state["messages"])
            # Add current user input
            messages.append(HumanMessage(content=user_message))
            
            # Invoke Ollama LLM with message format
            response = await self.ollama_llm.ainvoke(messages)
            
            print("✅ Ollama Agent: Response generated")
            
            # Handle both string and object responses from Ollama
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Return state updates as a dictionary - this is the LangGraph pattern
            return {
                "response": response_text,
                "messages": [AIMessage(content=response_text)],
                "error": None
            }
            
        except Exception as e:
            print(f"❌ Ollama Agent error: {e}")
            return {
                "response": "I apologize, but I'm having trouble processing your request right now. Please try again.",
                "messages": [AIMessage(content="I apologize, but I'm having trouble processing your request right now. Please try again.")],
                "error": str(e)
            }
    
    async def _booking_processor_node(self, state: AgentState) -> AgentState:
        """Process booking actions using extracted intents with conversational enhancement"""
        print("📋 Booking Processor: Processing...")
        
        try:
            # Extract intent from user message
            intent = await self.intent_extractor.extract_booking_intent(state["user_input"])
            print(f"🔍 Extracted intent: {intent}")
            
            # Get or initialize booking information from session
            session_booking = state["session_data"].get("booking_info", {})
            
            # Merge new intent with existing session data
            if intent:
                for key, value in intent.items():
                    if value:  # Only update if we have a value
                        session_booking[key] = value
            
            # Update session data
            updated_session = state["session_data"].copy()
            updated_session["booking_info"] = session_booking
            
            # Prepare state updates
            updates = {
                "booking_intent": intent,
                "session_data": updated_session,
                "error": None
            }
            
            # Check if this is an explicit booking action request
            if intent and intent.get('action') in ['check_availability', 'book', 'get_booking', 'update_booking', 'cancel_booking']:
                print(f"📋 Processing direct action: {intent.get('action')}")
                # Process direct booking action
                response, booking_data, availability_data = await self._process_booking_action(
                    intent, updated_session
                )
                
                # Add booking results to state updates
                if booking_data:
                    updates["booking_data"] = booking_data
                if availability_data:
                    updates["availability_data"] = availability_data
                
                # Override response if we have booking results
                if response:
                    updates["response"] = response
                    updates["messages"] = [AIMessage(content=response)]
                    
            # Check if we need conversational flow or direct booking
            elif self._should_use_conversational_flow(session_booking, state["user_input"]):
                # Let the AI handle the conversation naturally
                print("📋 Using conversational flow")
                return updates
            
            print("✅ Booking Processor: Completed")
            return updates
            
        except Exception as e:
            print(f"❌ Booking Processor error: {e}")
            return {"error": str(e)}
    
    def _should_use_conversational_flow(self, session_booking: dict, user_input: str) -> bool:
        """Determine if we should use conversational flow or direct booking"""
        required_fields = ['restaurant', 'date', 'time', 'party_size', 'name', 'email']
        missing_fields = [field for field in required_fields if not session_booking.get(field)]
        
        # Use conversational flow if:
        # 1. We're missing required information (including restaurant selection)
        # 2. User didn't provide complete booking details in one message
        # 3. User is asking questions or being conversational
        
        conversational_indicators = ['?', 'can you', 'could you', 'please', 'help', 'what', 'when', 'how', 'which', 'where']
        is_conversational = any(indicator in user_input.lower() for indicator in conversational_indicators)
        
        return len(missing_fields) > 0 or is_conversational
    
    async def _process_booking_action(self, intent: dict, session_data: dict) -> Tuple[str, Optional[dict], Optional[dict]]:
        """Process booking actions and return response with booking/availability data"""
        try:
            if intent.get('action') == 'check_availability':
                if intent.get('date') and intent.get('party_size'):
                    normalized_date = self.intent_extractor.normalize_date_text(intent['date'])
                    if not normalized_date:
                        return "Please provide a valid date.", None, None
                    
                    # Check availability across all restaurants if no specific restaurant chosen
                    if intent.get('restaurant'):
                        restaurant_name = intent['restaurant']
                        availability_result = await booking_client.check_availability(normalized_date, intent['party_size'], restaurant_name)
                        
                        if 'error' not in availability_result:
                            available_slots = availability_result.get('available_slots', [])
                            available_times = [slot for slot in available_slots if slot.get('available', False)]
                            
                            if available_times:
                                time_options = [slot['time'] for slot in available_times]
                                restaurant_info = booking_client.get_restaurant_info(restaurant_name)
                                
                                availability_data = {
                                    'date': normalized_date,
                                    'party_size': intent['party_size'],
                                    'restaurant': restaurant_name,
                                    'available_slots': available_slots,
                                    'available_times': time_options
                                }
                                
                                return f"Perfect! {restaurant_info.get('name', restaurant_name)} has availability on {normalized_date} for {intent['party_size']} people. Available times: {', '.join(time_options[:5])}{'...' if len(time_options) > 5 else ''}.", None, availability_data
                            else:
                                return f"I'm sorry, {restaurant_name} doesn't have availability on {normalized_date} for {intent['party_size']} people. Would you like to try a different date or restaurant?", None, None
                        else:
                            return f"I'm sorry, I couldn't check availability right now. {availability_result['error']}", None, None
                    else:
                        # Check all restaurants and recommend those with availability
                        available_restaurants = await booking_client.get_restaurants_with_availability(normalized_date, intent['party_size'])
                        
                        if available_restaurants:
                            restaurant_names = list(available_restaurants.keys())
                            availability_data = {
                                'date': normalized_date,
                                'party_size': intent['party_size'],
                                'available_restaurants': available_restaurants
                            }
                            
                            if len(restaurant_names) == 1:
                                restaurant_id = restaurant_names[0]
                                restaurant = available_restaurants[restaurant_id]
                                time_options = [slot['time'] for slot in restaurant['available_times']]
                                return f"Good news! {restaurant['name']} has availability on {normalized_date} for {intent['party_size']} people. Available times: {', '.join(time_options[:5])}{'...' if len(time_options) > 5 else ''}.", None, availability_data
                            else:
                                restaurant_list = [available_restaurants[r]['name'] for r in restaurant_names[:3]]
                                return f"Great! I found availability on {normalized_date} for {intent['party_size']} people at: {', '.join(restaurant_list)}{'...' if len(restaurant_names) > 3 else ''}. Which restaurant interests you?", None, availability_data
                        else:
                            return f"I'm sorry, none of our restaurants have availability on {normalized_date} for {intent['party_size']} people. Would you like to try a different date?", None, None
                else:
                    return "To check availability, I need both the date and party size.", None, None
            
            elif intent.get('action') == 'book':
                required_fields = ['restaurant', 'date', 'time', 'party_size', 'name', 'email']
                missing_fields = [field for field in required_fields if not intent.get(field)]
                
                print(f"Booking intent fields: {intent}")
                print(f"Missing fields: {missing_fields}")
                
                if missing_fields:
                    missing_items = []
                    for field in missing_fields:
                        if field == 'restaurant':
                            missing_items.append('restaurant choice')
                        elif field == 'party_size':
                            missing_items.append('party size')
                        else:
                            missing_items.append(field)
                    return f"I'd be happy to help you make a reservation! I still need: {', '.join(missing_items)}. Could you please provide this information?", None, None
                
                # Normalize date first
                normalized_date = self.intent_extractor.normalize_date_text(intent['date'])
                if not normalized_date:
                    return "Please provide a valid date (e.g., 'tomorrow', 'January 15', '2025-01-15').", None, None
                
                # Check availability first
                # Get restaurant info
                restaurant_name = intent.get('restaurant', RESTAURANT_NAME)
                restaurant_info = booking_client.get_restaurant_info(restaurant_name)
                
                availability_check = await booking_client.check_availability(normalized_date, intent['party_size'], restaurant_name)
                
                if 'error' in availability_check:
                    return f"I'm sorry, I couldn't check availability right now: {availability_check['error']}. Please try again later.", None, None
                
                available_slots = availability_check.get('available_slots', [])
                if not available_slots:
                    return f"I'm sorry, there are no available slots for {intent['party_size']} people on {normalized_date}. Would you like to try a different date?", None, None
                
                # Create booking
                customer_info = {
                    'name': intent['name'],
                    'email': intent['email'],
                    'phone': intent.get('phone', ''),
                    'special_requests': intent.get('special_requests', '')
                }
                
                booking_result = await booking_client.create_booking(
                    normalized_date, intent['time'], intent['party_size'], customer_info, restaurant_name
                )
                
                if 'error' not in booking_result:
                    booking_ref = booking_result.get('booking_reference')
                    
                    if booking_ref:
                        booking_data = {
                            'date': normalized_date,
                            'time': intent['time'],
                            'party': intent['party_size'],
                            'reference': booking_ref,
                            'status': booking_result.get('status', 'confirmed'),
                            'restaurant': 'TheHungryUnicorn',
                            'verified': True
                        }
                        
                        restaurant_display_name = restaurant_info.get('name', restaurant_name)
                        success_message = f"🎉 **RESERVATION CONFIRMED!**\n\n"
                        success_message += f"🍽️ Restaurant: {restaurant_display_name}\n"
                        success_message += f"📅 Date: {normalized_date}\n"
                        success_message += f"🕐 Time: {intent['time']}\n"
                        success_message += f"👥 Party Size: {intent['party_size']} people\n"
                        success_message += f"👤 Customer: {intent['name']}\n"
                        success_message += f"🎫 Reference: {booking_ref}\n"
                        success_message += f"✅ Your booking has been confirmed!"
                        
                        return success_message, booking_data, None
                    else:
                        return "❌ Booking was processed but no reference number was returned. Please contact support.", None, None
                else:
                    error_msg = booking_result.get('error', 'Unknown error')
                    return f"❌ Booking Failed: {error_msg}", None, None
            
            elif intent.get('action') == 'get_booking':
                booking_ref = intent.get('booking_reference')
                if not booking_ref:
                    return "To check your booking, I need your booking reference number. Can you provide it?", None, None
                
                # Try to get booking from each restaurant (since we don't know which one)
                booking_found = None
                found_restaurant = None
                
                for restaurant_id in booking_client._restaurant_metadata.keys():
                    booking_result = await booking_client.get_booking(booking_ref, restaurant_id)
                    if 'error' not in booking_result:
                        booking_found = booking_result
                        found_restaurant = restaurant_id
                        break
                
                if booking_found:
                    restaurant_info = booking_client.get_restaurant_info(found_restaurant)
                    customer = booking_found.get('customer', {})
                    
                    booking_data = {
                        'reference': booking_found.get('booking_reference'),
                        'date': booking_found.get('visit_date'),
                        'time': booking_found.get('visit_time'),
                        'party': booking_found.get('party_size'),
                        'status': booking_found.get('status'),
                        'restaurant': found_restaurant,
                        'customer_name': f"{customer.get('first_name', '')} {customer.get('surname', '')}".strip()
                    }
                    
                    # Check booking status and customize response accordingly
                    booking_status = booking_found.get('status', 'confirmed').lower()
                    
                    if booking_status == 'cancelled':
                        response = f"❌ **BOOKING CANCELLED**\n\n"
                        response += f"🎫 Reference: {booking_found.get('booking_reference')}\n"
                        response += f"🍽️ Restaurant: {restaurant_info.get('name', found_restaurant)}\n"
                        response += f"📅 Original Date: {booking_found.get('visit_date')}\n"
                        response += f"🕐 Original Time: {booking_found.get('visit_time')}\n"
                        response += f"👥 Party Size: {booking_found.get('party_size')} people\n"
                        response += f"❌ Status: CANCELLED\n"
                        
                        # Add cancellation details if available
                        if booking_found.get('cancelled_at'):
                            response += f"📅 Cancelled On: {booking_found.get('cancelled_at')}\n"
                        if booking_found.get('cancellation_reason'):
                            response += f"📝 Reason: {booking_found.get('cancellation_reason')}\n"
                        
                        response += f"\n💔 This booking has already been cancelled. If you'd like to make a new reservation, I'd be happy to help!"
                        
                    else:
                        # Active booking
                        status_emoji = "✅" if booking_status == 'confirmed' else "🔄"
                        response = f"📋 **BOOKING DETAILS**\n\n"
                        response += f"🎫 Reference: {booking_found.get('booking_reference')}\n"
                        response += f"🍽️ Restaurant: {restaurant_info.get('name', found_restaurant)}\n"
                        response += f"📅 Date: {booking_found.get('visit_date')}\n"
                        response += f"🕐 Time: {booking_found.get('visit_time')}\n"
                        response += f"👥 Party Size: {booking_found.get('party_size')} people\n"
                        response += f"👤 Customer: {customer.get('first_name', '')} {customer.get('surname', '')}\n"
                        response += f"📧 Email: {customer.get('email', 'Not provided')}\n"
                        response += f"📱 Phone: {customer.get('mobile', 'Not provided')}\n"
                        response += f"{status_emoji} Status: {booking_status.title()}"
                        
                        if booking_found.get('special_requests'):
                            response += f"\n📝 Special Requests: {booking_found.get('special_requests')}"
                        
                        # Add last updated info if available
                        if booking_found.get('updated_at') and booking_status == 'updated':
                            response += f"\n🔄 Last Updated: {booking_found.get('updated_at')}"
                    
                    return response, booking_data, None
                else:
                    return f"❌ I couldn't find a booking with reference {booking_ref}. Please check the reference number and try again.", None, None
            
            elif intent.get('action') == 'update_booking':
                booking_ref = intent.get('booking_reference')
                if not booking_ref:
                    return "To modify your booking, I need your booking reference number. Can you provide it?", None, None
                
                # First check if booking exists and its status
                booking_exists = None
                found_restaurant_check = None
                
                for restaurant_id in booking_client._restaurant_metadata.keys():
                    booking_result = await booking_client.get_booking(booking_ref, restaurant_id)
                    if 'error' not in booking_result:
                        booking_exists = booking_result
                        found_restaurant_check = restaurant_id
                        break
                
                if booking_exists:
                    booking_status = booking_exists.get('status', '').lower()
                    if booking_status == 'cancelled':
                        restaurant_info = booking_client.get_restaurant_info(found_restaurant_check)
                        return f"❌ **BOOKING ALREADY CANCELLED**\n\nBooking {booking_ref} at {restaurant_info.get('name', found_restaurant_check)} has already been cancelled and cannot be modified. If you'd like to make a new reservation, I'd be happy to help!", None, None
                
                # Extract what they want to change
                updates = {}
                
                # Only process date if it looks like a real date
                if intent.get('date'):
                    date_text = intent['date'].strip()
                    # Skip obviously invalid date fragments like "to 8"
                    if len(date_text) > 3 and not date_text.startswith('to '):
                        normalized_date = self.intent_extractor.normalize_date_text(date_text)
                        if normalized_date:
                            updates['date'] = normalized_date
                        else:
                            return f"Please provide a valid date for the change. '{date_text}' is not a valid date.", None, None
                
                if intent.get('time'):
                    updates['time'] = intent['time']
                
                if intent.get('party_size'):
                    updates['party_size'] = intent['party_size']
                
                if not updates:
                    return "What would you like to change about your booking? Date, time, or party size?", None, None
                
                # Try to update booking in each restaurant
                update_successful = False
                found_restaurant = None
                
                for restaurant_id in booking_client._restaurant_metadata.keys():
                    update_result = await booking_client.update_booking(booking_ref, updates, restaurant_id)
                    if 'error' not in update_result:
                        update_successful = True
                        found_restaurant = restaurant_id
                        break
                
                if update_successful:
                    restaurant_info = booking_client.get_restaurant_info(found_restaurant)
                    
                    response = f"✅ **BOOKING UPDATED!**\n\n"
                    response += f"🎫 Reference: {booking_ref}\n"
                    response += f"🍽️ Restaurant: {restaurant_info.get('name', found_restaurant)}\n"
                    
                    if 'date' in updates:
                        response += f"📅 New Date: {updates['date']}\n"
                    if 'time' in updates:
                        response += f"🕐 New Time: {updates['time']}\n"
                    if 'party_size' in updates:
                        response += f"👥 New Party Size: {updates['party_size']} people\n"
                    
                    response += f"🎉 Your booking has been successfully updated!"
                    
                    booking_data = {
                        'reference': booking_ref,
                        'status': 'updated',
                        'restaurant': found_restaurant,
                        'changes': updates
                    }
                    
                    return response, booking_data, None
                else:
                    return f"❌ I couldn't update booking {booking_ref}. Please check the reference number and try again.", None, None
            
            elif intent.get('action') == 'cancel_booking':
                booking_ref = intent.get('booking_reference')
                if not booking_ref:
                    return "To cancel your booking, I need your booking reference number. Can you provide it?", None, None
                
                # First check if booking exists and its status
                booking_exists = None
                found_restaurant_check = None
                
                for restaurant_id in booking_client._restaurant_metadata.keys():
                    booking_result = await booking_client.get_booking(booking_ref, restaurant_id)
                    if 'error' not in booking_result:
                        booking_exists = booking_result
                        found_restaurant_check = restaurant_id
                        break
                
                if booking_exists:
                    booking_status = booking_exists.get('status', '').lower()
                    if booking_status == 'cancelled':
                        restaurant_info = booking_client.get_restaurant_info(found_restaurant_check)
                        return f"❌ **BOOKING ALREADY CANCELLED**\n\nBooking {booking_ref} at {restaurant_info.get('name', found_restaurant_check)} has already been cancelled. No further action is needed.", None, None
                
                # Try to cancel booking in each restaurant
                cancel_successful = False
                found_restaurant = None
                
                for restaurant_id in booking_client._restaurant_metadata.keys():
                    cancel_result = await booking_client.cancel_booking(booking_ref, 1, restaurant_id)  # Reason 1: Customer Request
                    if 'error' not in cancel_result:
                        cancel_successful = True
                        found_restaurant = restaurant_id
                        break
                
                if cancel_successful:
                    restaurant_info = booking_client.get_restaurant_info(found_restaurant)
                    
                    response = f"❌ **BOOKING CANCELLED**\n\n"
                    response += f"🎫 Reference: {booking_ref}\n"
                    response += f"🍽️ Restaurant: {restaurant_info.get('name', found_restaurant)}\n"
                    response += f"📅 Cancellation: Confirmed\n"
                    response += f"💔 We're sorry to see you cancel. We hope to see you again soon!"
                    
                    booking_data = {
                        'reference': booking_ref,
                        'status': 'cancelled',
                        'restaurant': found_restaurant
                    }
                    
                    return response, booking_data, None
                else:
                    return f"❌ I couldn't cancel booking {booking_ref}. Please check the reference number and try again.", None, None
            
            return "I understand you're interested in booking. How can I help you with your reservation?", None, None
            
        except Exception as e:
            return f"I apologize, but I encountered an issue processing your request: {str(e)}", None, None
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for AI agents"""
        return """You are TableBooker, a friendly and conversational booking assistant for our restaurant group.

CONVERSATION STYLE:
- Be warm, natural, and engaging like a real restaurant host
- Ask for information gradually and conversationally, not all at once
- Acknowledge what the user has already provided
- Show enthusiasm about their dining plans
- Use casual, friendly language while remaining professional

AVAILABLE RESTAURANTS:
- The Hungry Unicorn: Upscale modern European cuisine ($$$$)
- Pizza Palace: Authentic Italian pizzas and pasta ($$$)
- Sushi Zen: Fresh sushi and Japanese cuisine ($$$$) 
- Cafe Bistro: Casual French bistro with daily specials ($$)

CONVERSATION FLOW:
1. If no restaurant specified, ask about cuisine preference or show restaurant options
2. Once restaurant is chosen, ask about preferred date/time
3. Once you have date/time, ask about party size
4. After date/time/party size, ask for name and contact info
5. Confirm all details before making the reservation

IMPORTANT AVAILABILITY RULES:
- ONLY recommend restaurants that actually have availability for the requested date/time/party size
- ONLY suggest time slots that are confirmed available in our system
- If a restaurant has no availability, suggest alternative restaurants or dates
- Always mention specific available time slots when known

BOOKING MANAGEMENT CAPABILITIES:
- Check availability across all restaurants
- Make new reservations
- Look up existing bookings by reference number
- Modify bookings (change date, time, or party size)
- Cancel bookings with confirmation
- Handle multi-restaurant queries efficiently

RESTAURANT SELECTION EXAMPLES:
- "We have several wonderful restaurants! Are you in the mood for European, Italian, Japanese, or French cuisine?"
- "I can help you choose! What type of dining experience are you looking for today?"
- "Great! The Hungry Unicorn specializes in modern European cuisine. When were you thinking of dining?"

BOOKING FLOW EXAMPLES:
- "Perfect choice! What date were you thinking for your dinner?"
- "Excellent! And how many people will be joining you?"
- "Great! Could I get your name for the reservation?"
- "Almost done! I just need your email to confirm the booking."

BOOKING LOOKUP/MODIFICATION EXAMPLES:
- "I can help you check your reservation. What's your booking reference?"
- "No problem! I can update your booking. What would you like to change?"
- "I understand you need to cancel. Let me process that for you."

Remember: Help them choose the right restaurant first, then build the conversation naturally. Show genuine interest in matching them with the perfect dining experience. Always base recommendations on actual availability data. For booking changes, be understanding and helpful."""
    
    async def process_message(self, message: str, session_data: dict = None) -> Tuple[str, Optional[dict], Optional[dict], dict]:
        """Process a message through the LangGraph agent"""
        session_data = session_data or {}
        
        # Prepare initial state
        initial_state = AgentState(
            messages=[HumanMessage(content=message)],
            user_input=message,
            session_data=session_data,
            booking_intent=None,
            response="",
            booking_data=None,
            availability_data=None,
            error=None
        )
        
        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)
        
        return (
            final_state["response"],
            final_state.get("booking_data"),
            final_state.get("availability_data"), 
            final_state["session_data"]
        )

# Lazy initialization to prevent duplication during startup
_agent_instance = None

def get_agent():
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = BookingAgent()
    return _agent_instance

@app.get("/")
async def root():
    """API information"""
    return {
        "service": "TableBooker AI Agent API (LangGraph + Ollama)",
        "version": "1.0.0",
        "status": "running",
        "ai_framework": "LangGraph",
        "ai_provider": "Ollama llama3.1:8b",
        "features": ["Restaurant booking", "Natural language understanding", "Multi-restaurant support", "Booking management"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test AI providers
        openai_status = agent.openai_llm is not None
        ollama_status = False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
                ollama_status = response.status_code == 200
        except:
            pass
        
        return {
            "status": "healthy",
            "service": "TableBooker AI Agent API (LangGraph)",
            "ai_framework": "LangGraph",
            "ai_providers": {
                "openai_available": openai_status,
                "ollama_available": ollama_status,
                "simple_mode": True
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "TableBooker AI Agent API (LangGraph)",
            "error": str(e)
        }

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with the LangGraph-powered AI agent
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
        
        # Process message through LangGraph agent
        response_message, booking_data, availability_data, updated_session = await get_agent().process_message(
            request.message,
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
            availability_data=availability_data,
            ai_mode="ollama"
        )
        
        print(f"🤖 LangGraph Chat - User: {request.message}")
        print(f"🤖 LangGraph Response (ollama): {response_message[:100]}...")
        
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
    
    suggestions = []
    
    # Priority suggestions based on data presence
    if booking_data:
        suggestions = ["View booking details", "Modify reservation", "Cancel reservation"]
    elif availability_data:
        suggestions = ["Book this time", "Check different times", "Try different party size"]
    else:
        # Context-aware suggestions
        if any(word in user_lower for word in ['hello', 'hi', 'start']):
            suggestions = ["Check availability this weekend", "Make a reservation", "Check my booking"]
        elif any(word in user_lower for word in ['book', 'reserve', 'table']):
            suggestions = ["Check availability first", "Provide booking details", "Restaurant info"]
        elif any(word in user_lower for word in ['availability', 'check', 'free', 'available']):
            suggestions = ["Book available time", "Try different date", "Change party size"]
        else:
            suggestions = ["Check availability", "Make reservation", "Check my booking"]
    
    return suggestions[:3]  # Limit to 3 suggestions

@app.get("/restaurants")
async def get_restaurants():
    """Get available restaurants"""
    return {
        "restaurants": booking_client.get_available_restaurants(),
        "count": len(booking_client.get_available_restaurants())
    }

@app.get("/ai-status")
async def ai_status():
    """Check Ollama status"""
    ollama_status = False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            ollama_status = response.status_code == 200
    except:
        pass
        
    return {
        "ai_framework": "LangGraph",
        "provider": "Ollama",
        "ollama": {
            "available": ollama_status,
            "model": MODEL_NAME if ollama_status else None,
            "base_url": OLLAMA_BASE_URL
        }
    }

@app.get("/graph-structure")
async def graph_structure():
    """Get the LangGraph structure visualization - following official patterns"""
    try:
        # Get graph structure (following LangGraph documentation pattern)
        graph_dict = agent.graph.get_graph().to_json()
        
        return {
            "framework": "LangGraph",
            "graph_structure": graph_dict,
            "nodes": [
                {"name": "router", "type": "decision", "description": "Routes to appropriate AI provider"},
                {"name": "openai_agent", "type": "llm", "description": "OpenAI GPT-3.5-turbo processing"},
                {"name": "ollama_agent", "type": "llm", "description": "Ollama local LLM processing"},
                {"name": "simple_agent", "type": "rule-based", "description": "Simple pattern matching"},
                {"name": "booking_processor", "type": "action", "description": "Processes booking operations"}
            ],
            "edges": [
                {"from": "START", "to": "router"},
                {"from": "router", "to": "openai_agent", "condition": "openai available"},
                {"from": "router", "to": "ollama_agent", "condition": "ollama available"},
                {"from": "router", "to": "simple_agent", "condition": "fallback mode"},
                {"from": "*_agent", "to": "booking_processor"},
                {"from": "booking_processor", "to": "END"}
            ]
        }
    except Exception as e:
        return {"error": f"Failed to get graph structure: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting TableBooker AI Agent with LangGraph + Ollama")
    print("📡 Server will run on http://localhost:8000")
    print("🤖 AI Framework: LangGraph")
    print("🦙 AI Provider: Ollama")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )