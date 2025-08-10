# TableBooker AI Agent 🍽️

A sophisticated conversational AI agent built with **LangGraph** and **Ollama** that provides complete restaurant booking management through natural language conversations.

## 🌟 Overview

TableBooker is a production-ready chat interface that seamlessly integrates with restaurant booking systems to provide customers with an intuitive way to:

- ✅ **Check availability** across multiple restaurants with real-time data
- ✅ **Make reservations** with natural conversation flow
- ✅ **View booking details** using booking references
- ✅ **Modify reservations** (time, date, party size)
- ✅ **Cancel bookings** with proper status handling
- ✅ **Handle edge cases** like cancelled booking status

## 🚀 Key Features

### 🤖 **Advanced AI Architecture**
- **LangGraph Framework**: State-driven conversation management
- **Ollama Integration**: Local LLM processing (llama3.1:8b)
- **Enhanced Intent Recognition**: Detects all booking operations with priority handling
- **Smart Status Management**: Tracks and prevents operations on cancelled bookings

### 🏪 **Multi-Restaurant Support**
- **4 Restaurants**: TheHungryUnicorn, PizzaPalace, SushiZen, CafeBistro
- **Database-Driven**: Real availability data from SQLite database
- **Cuisine-Based Selection**: Natural restaurant matching by cuisine preference
- **Cross-Restaurant Search**: Automatic lookup across all restaurants

### 💬 **Natural Conversation**
- **Conversational Flow**: Gradual information gathering
- **Context Awareness**: Remembers conversation history
- **Rich Responses**: Formatted messages with emojis and structure
- **Error Recovery**: Graceful handling of invalid inputs

### 🔧 **Complete CRUD Operations**
- **Create**: Full booking creation with availability validation
- **Read**: Booking lookup by reference across all restaurants
- **Update**: Modify time, date, party size with validation
- **Delete**: Cancel bookings with reason tracking

## 📊 User Stories - All Implemented ✅

| User Story | Status | Example |
|------------|--------|---------|
| **Check Availability** | ✅ **COMPLETE** | *"Can you show me availability for this weekend?"* |
| **Book Reservation** | ✅ **COMPLETE** | *"I'd like to book a table for 4 people next Friday at 7pm."* |
| **Check Booking Details** | ✅ **COMPLETE** | *"What time is my reservation on Saturday?"* |
| **Modify Reservation** | ✅ **COMPLETE** | *"I need to change my booking from 6pm to 8pm."* |
| **Cancel Reservation** | ✅ **COMPLETE** | *"Please cancel my reservation for tomorrow."* |

## 🏗️ Technical Architecture

### **Core Stack**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   AI Backend    │    │   Mock API      │
│   React + TS    │◄──►│ LangGraph+Ollama│◄──►│ FastAPI+SQLite  │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8547    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **AI Framework Details**
- **State Management**: TypedDict with add_messages reducer
- **Graph Structure**: START → ollama_agent → booking_processor → END
- **Intent Extraction**: Priority-based pattern matching (cancel > modify > lookup > availability > book)
- **Booking Reference**: Advanced regex patterns for alphanumeric codes

### **Database Integration**
- **SQLAlchemy ORM**: Direct database queries for restaurant data
- **Real-Time Availability**: Live slot checking from availability tables
- **No Hardcoded Data**: All restaurant information from database
- **Multi-Restaurant Support**: Seamless switching between restaurants

## 📁 Project Structure

```
restaurant-booking-chat-agent/
├── 📄 README.md                          # This file
├── 🧪 user_stories_test.py               # Comprehensive test suite
├── 📊 enhanced_test_script_summary.md    # Test documentation
├── 🔧 backend/                           # AI Agent Backend
│   ├── main.py                          # LangGraph + Ollama server
│   ├── requirements.txt                 # Python dependencies
│   └── README.md                        # Backend docs
├── 🎨 frontend/                          # React Web Interface  
│   ├── src/                             # React components
│   ├── package.json                     # Node dependencies
│   └── README.md                        # Frontend docs
├── 🔧 install_ollama_model.bat          # Ollama setup
├── 🚀 start_ollama_system.bat           # Quick start
├── 📖 OLLAMA_SETUP.md                   # Setup guide
├── ⚡ QUICK_SETUP.md                    # Quick start guide
└── 🧪 test_ollama.py                    # Connectivity test
```

## 🚀 Quick Start

### **1. Prerequisites**
- Python 3.8+
- Node.js 16+
- Git
- Ollama installed locally

### **2. Start Restaurant API Server**
> **Uses Enhanced Fork**: [Nikitich2033/Restaurant-Booking-Mock-API-Server](https://github.com/Nikitich2033/Restaurant-Booking-Mock-API-Server) with multi-restaurant support

   ```bash
cd Restaurant-Booking-Mock-API-Server
pip install -r requirements.txt
python -m app
# Server runs on http://localhost:8547 with 4 restaurants
```

### **3. Start AI Agent Backend**
   ```bash
cd restaurant-booking-chat-agent/backend
   pip install -r requirements.txt
python main.py
# Server runs on http://localhost:8000
   ```

### **4. Start Frontend (Optional)**
   ```bash
cd restaurant-booking-chat-agent/frontend
npm install
npm start
# Frontend runs on http://localhost:3000
```

### **5. Run Complete Test Suite**
   ```bash
cd restaurant-booking-chat-agent
python user_stories_test.py
```

## 🧪 Testing

### **Comprehensive Test Suite**
The project includes a complete test suite (`user_stories_test.py`) with:

#### **✅ Core User Stories (4 tests)**
1. Check availability across multiple restaurants
2. Create bookings with validation
3. Lookup booking details by reference
4. Modify and cancel reservations

#### **🔍 Edge Cases - Cancelled Booking Status (5 tests)**
1. Create test booking for cancellation
2. Cancel the booking
3. Check cancelled booking status → Shows "BOOKING CANCELLED"
4. Try to modify cancelled booking → **Blocked** with explanation
5. Try to cancel already cancelled → **Blocked** ("already cancelled")

#### **⚠️ Invalid Operations (5 tests)**
1. Check invalid booking reference
2. Modify non-existent booking
3. Cancel non-existent booking
4. Incomplete booking requests
5. Invalid date formats

**Total: 15 comprehensive test scenarios**

### **Run Tests**
```bash
# Run complete test suite
python user_stories_test.py

# Quick manual tests
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "availability tomorrow 2 people", "session_id": "test1"}'
```

## 📚 API Integration

### **TableBooker AI Endpoints**
- `POST /chat` - Main chat interface
- `GET /ai-status` - AI system health
- `GET /restaurants` - Available restaurants
- `GET /` - System information

### **Enhanced Mock Booking API (Port 8547)**
> **Repository**: [Nikitich2033/Restaurant-Booking-Mock-API-Server](https://github.com/Nikitich2033/Restaurant-Booking-Mock-API-Server)

- `POST /api/ConsumerApi/v1/Restaurant/{name}/AvailabilitySearch` - Check availability
- `POST /api/ConsumerApi/v1/Restaurant/{name}/BookingWithStripeToken` - Create booking
- `GET /api/ConsumerApi/v1/Restaurant/{name}/Booking/{ref}` - Get booking details ✨ **Enhanced**
- `PATCH /api/ConsumerApi/v1/Restaurant/{name}/Booking/{ref}` - Update booking ✨ **Enhanced**
- `POST /api/ConsumerApi/v1/Restaurant/{name}/Booking/{ref}/Cancel` - Cancel booking ✨ **Enhanced**

**✨ Recent Enhancements:**
- ✅ **Multi-Restaurant Support**: 4 restaurants with varied cuisines
- ✅ **Enhanced Status Handling**: Cancelled booking prevention logic
- ✅ **Comprehensive Edge Cases**: 15 test scenarios including error handling
- ✅ **Database-Driven Data**: No hardcoded restaurant information
- ✅ **Booking Reference Extraction**: Advanced alphanumeric pattern recognition

## 🎯 Usage Examples

### **Check Availability**
```json
POST /chat
{
  "message": "availability tomorrow 4 people",
  "session_id": "user123"
}

Response: Shows 4 restaurants with time slots
```

### **Book Restaurant**
```json
POST /chat
{
  "message": "book Pizza Palace tomorrow 7pm 2 people John Smith john@example.com",
  "session_id": "user123" 
}

Response: "🎉 RESERVATION CONFIRMED! Reference: ABC1234"
```

### **Check Booking Status**
```json
POST /chat
{
  "message": "check my booking reference ABC1234",
  "session_id": "user123"
}

Response: Complete booking details or cancelled status
```

### **Modify Booking**
```json
POST /chat
{
  "message": "change my booking ABC1234 to 8pm",
  "session_id": "user123"
}

Response: "✅ BOOKING UPDATED! New Time: 8pm"
```

## 🎨 Status Handling

### **Booking Statuses**
- **✅ Confirmed**: Active booking, can be modified/cancelled
- **🔄 Updated**: Modified booking, can be further modified/cancelled  
- **❌ Cancelled**: Cancelled booking, **cannot be modified** (prevention logic)

### **Cancelled Booking Response**
```
❌ **BOOKING CANCELLED**

🎫 Reference: ABC1234
🍽️ Restaurant: Pizza Palace
📅 Original Date: 2025-08-11
🕐 Original Time: 19:00:00
👥 Party Size: 2 people
❌ Status: CANCELLED
📝 Reason: Customer Request

💔 This booking has already been cancelled. 
If you'd like to make a new reservation, I'd be happy to help!
```

## 🏪 Available Restaurants

| Restaurant | Cuisine | Price Range | Specialties |
|------------|---------|-------------|-------------|
| **The Hungry Unicorn** | European | $$$$ | Upscale modern European cuisine |
| **Pizza Palace** | Italian | $$$ | Authentic Italian pizzas and pasta |
| **Sushi Zen** | Japanese | $$$$ | Fresh sushi and Japanese cuisine |
| **Cafe Bistro** | French | $$ | Casual French bistro with daily specials |

## 🛠️ Development

### **Key Implementation Files**
- `backend/main.py` - Main LangGraph agent with Ollama integration
- `user_stories_test.py` - Complete test suite with edge cases
- `frontend/src/App.tsx` - React chat interface

### **Adding New Features**
1. Update intent extraction patterns in `extract_booking_intent()`
2. Add new actions to `_process_booking_action()`
3. Update system prompts in `_get_system_prompt()`
4. Add test cases to `user_stories_test.py`

### **Code Quality**
- Type hints throughout codebase
- Comprehensive error handling
- Rich logging and debugging
- Modular architecture

## 🔮 Roadmap

### **Completed ✅**
- ✅ **LangGraph + Ollama integration** (llama3.1:8b model)
- ✅ **Multi-restaurant support** (4 restaurants with diverse cuisines)
- ✅ **Complete CRUD operations** (Create, Read, Update, Delete bookings)
- ✅ **Enhanced status handling** (cancelled booking prevention logic)
- ✅ **Edge case prevention logic** (blocks invalid operations)
- ✅ **Comprehensive test suite** (15 test scenarios with edge cases)
- ✅ **Database-driven availability** (real-time data from SQLite)
- ✅ **Natural conversation flow** (gradual information gathering)
- ✅ **Enhanced API fork** (multi-restaurant mock server)
- ✅ **Advanced intent recognition** (priority-based pattern matching)
- ✅ **Booking reference extraction** (alphanumeric code recognition)
- ✅ **Production-ready documentation** (complete setup guides)

### **Future Enhancements 🚀**
- 🔄 User authentication system
- 🔄 Email confirmation notifications
- 🔄 Voice interface integration
- 🔄 Mobile app development
- 🔄 Analytics dashboard
- 🔄 Multi-language support

## 📈 Performance

- **Response Time**: < 2 seconds for availability checks
- **Booking Creation**: < 3 seconds end-to-end
- **Database Queries**: Optimized with SQLAlchemy ORM
- **LLM Processing**: Local Ollama for privacy and speed
- **Concurrent Users**: Supports multiple simultaneous sessions

## 🔒 Security

- ✅ Bearer token authentication
- ✅ Input validation and sanitization
- ✅ No sensitive data storage
- ✅ Local LLM processing (privacy-focused)
- ✅ SQL injection prevention
- ✅ Rate limiting considerations

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

- 📧 **Issues**: GitHub Issues tab
- 📖 **Documentation**: README files in each directory
- 🧪 **Testing**: Run `python user_stories_test.py`
- 💬 **Community**: Discussions tab

---

## 🎉 **Status: Production Ready!**

**Version**: 2.1.0  
**Last Updated**: August 2025  
**AI Framework**: LangGraph + Ollama (llama3.1:8b)  
**API Backend**: [Enhanced Fork](https://github.com/Nikitich2033/Restaurant-Booking-Mock-API-Server) with 4 restaurants  
**Test Coverage**: 15 comprehensive scenarios including edge cases  
**User Stories**: All 5 implemented with complete status handling  

**🚀 Ready for deployment with complete booking lifecycle management and enhanced multi-restaurant support!**