# Restaurant Booking Chat Agent

A conversational AI agent that helps customers make and manage restaurant bookings through an intelligent chat interface.

## Overview

This project implements a chat-based booking system that integrates with a restaurant booking API to provide customers with a natural language interface for:

- Checking restaurant availability
- Making new reservations
- Viewing existing booking details
- Modifying or canceling reservations

## Features

### Core Functionality
- **Natural Language Processing**: Understands customer intent from conversational input
- **Multi-turn Conversations**: Maintains context across the entire booking session
- **API Integration**: Seamlessly connects to restaurant booking backend
- **Error Handling**: Gracefully manages API errors and invalid requests
- **Authentication**: Secure bearer token authentication with the booking API

### User Stories Supported
1. **Check Availability**: "Can you show me availability for this weekend?"
2. **Book Reservation**: "I'd like to book a table for 4 people next Friday at 7pm."
3. **Check Reservation**: "What time is my reservation on Saturday?"
4. **Modify Reservation**: "I need to change my booking from 6pm to 8pm."
5. **Cancel Reservation**: "Please cancel my reservation for tomorrow."

## Technical Stack

### Agent Framework
- **Framework**: [To be selected - LangGraph/CrewAI/Custom implementation]
- **LLM Integration**: Support for both cloud APIs and local models (Ollama, vLLM, llama.cpp)
- **State Management**: Persistent conversation context

### API Integration
- **Base URL**: `http://localhost:8547`
- **Restaurant**: TheHungryUnicorn
- **Booking System**: UnicornReservations
- **Authentication**: Bearer token
- **Content Type**: `application/x-www-form-urlencoded`

### Interface Options
- **Minimum**: Terminal/console-based chat interface
- **Bonus**: Web-based chat interface

## Project Structure

```
restaurant-booking-chat-agent/
├── README.md                          # Project overview
├── backend/                          # Ollama-powered AI backend
│   ├── main.py                       # FastAPI server with Ollama
│   ├── requirements.txt              # Backend dependencies
│   └── README.md                     # Backend documentation
├── frontend/                         # React web interface
│   ├── src/                          # React components
│   ├── package.json                  # Frontend dependencies
│   └── README.md                     # Frontend documentation
├── install_ollama_model.bat          # Ollama setup script
├── start_ollama_system.bat           # Quick start script
├── OLLAMA_SETUP.md                   # Ollama installation guide
├── QUICK_SETUP.md                    # Quick setup instructions
└── test_ollama.py                    # Ollama connectivity test
```

## Getting Started

### Prerequisites
- Python 3.8+
- Git
- Internet connection (for cloud LLM APIs) or local model setup

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nikitich2033/Booking_Chat_Task.git
   cd Booking_Chat_Task
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Start the mock booking server**
   ```bash
   cd Restaurant-Booking-Mock-API-Server
   python -m app
   ```
   The server will start on `http://localhost:8547`

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Run the chat agent**
   ```bash
   python src/main.py
   ```

## Design Rationale

### Framework Selection
*[To be documented after implementation]*

**Considerations:**
- **LangGraph**: Excellent for complex multi-step workflows and state management
- **CrewAI**: Great for multi-agent scenarios and role-based interactions
- **Custom Framework**: Maximum flexibility and control over agent behavior

### Architecture Decisions

**State Management**
- Persistent conversation context to handle multi-turn dialogues
- Session-based booking information storage
- Graceful handling of conversation interruptions

**Error Handling Strategy**
- API timeout and retry mechanisms
- User-friendly error messages
- Fallback options for failed operations

**Security Considerations**
- Secure token management
- Input validation and sanitization
- Rate limiting for API calls
- No storage of sensitive customer data

### Production Scalability

**Current Limitations:**
- Single-user session handling
- In-memory state storage
- Local API server dependency

**Production Enhancements:**
- Database-backed session storage
- Multi-user concurrent support
- Distributed API architecture
- Comprehensive logging and monitoring
- Load balancing and auto-scaling

## API Endpoints

The mock booking server provides the following endpoints:

- `GET /availability` - Check table availability
- `POST /booking` - Create new reservation
- `GET /booking/{id}` - Retrieve booking details
- `PUT /booking/{id}` - Modify existing booking
- `DELETE /booking/{id}` - Cancel reservation

*Detailed API documentation available in `Restaurant-Booking-Mock-API-Server/README.md`*

## Usage Examples

### Terminal Interface
```
> Hello! I'd like to make a reservation.
Agent: I'd be happy to help you make a reservation! Could you please tell me:
- What date would you like to dine?
- What time do you prefer?
- How many people will be in your party?

> I need a table for 4 people this Friday at 7 PM.
Agent: Let me check availability for 4 people this Friday at 7 PM...
[Checking availability...]
Great! I found availability for Friday at 7:00 PM for 4 people. Would you like me to book this for you?
```

### Web Interface
*[To be implemented as bonus feature]*

## Testing

```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/

# Run with coverage
python -m pytest --cov=src tests/
```

## Development

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement changes with tests
3. Update documentation
4. Submit pull request

### Code Quality
- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Maintain test coverage above 80%
- Use type hints where applicable

## Limitations and Future Improvements

### Current Limitations
- Single restaurant support (TheHungryUnicorn) through UnicornReservations booking system
- Basic natural language understanding
- Limited conversation memory
- No user authentication system

### Planned Improvements
- Multi-restaurant support
- Advanced NLP capabilities
- Persistent user profiles
- Voice interface integration
- Mobile app development
- Analytics and reporting dashboard

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or feature requests, please:
- Open an issue on GitHub
- Contact the development team
- Check the documentation in the `docs/` directory

## Acknowledgments

- Limita team for providing the technical assessment
- Restaurant-Booking-Mock-API-Server for the backend infrastructure
- Open source community for the agent frameworks and tools

---

**Status**: 🚧 Under Development
**Version**: 0.1.0
**Last Updated**: January 2025
