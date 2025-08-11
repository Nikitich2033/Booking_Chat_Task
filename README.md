# TableBooker AI Agent 🍽️

A production-ready conversational AI agent for restaurant booking management, built with **LangGraph** and **Ollama** to provide intelligent, context-aware booking services through natural language conversations.

## 📋 Overview

TableBooker is an enterprise-grade chat interface that transforms restaurant booking from a rigid form-based process into an intuitive, conversational experience. The system integrates with restaurant management APIs to provide real-time availability checking, intelligent booking creation, and comprehensive reservation management.

It is designed to work seamlessly with an enhanced Mock Booking API server fork that includes multi-restaurant support for 4 venues — TheHungryUnicorn, PizzaPalace, SushiZen, and CafeBistro. See the forked repository here: [Nikitich2033/Restaurant-Booking-Mock-API-Server](https://github.com/Nikitich2033/Restaurant-Booking-Mock-API-Server).

### **Core Capabilities**
- **Multi-Restaurant Support**: Seamlessly manage bookings across multiple restaurant locations
- **Natural Language Processing**: Understand and respond to conversational booking requests
- **Real-Time Availability**: Database-driven availability checking with instant responses
- **Complete CRUD Operations**: Create, read, update, and cancel reservations
- **Context-Aware Conversations**: Maintain conversation state across multiple turns
- **Edge Case Handling**: Intelligent management of cancelled bookings and policy questions

## 🚀 Getting Started

### **Prerequisites**
- Python 3.8+ with pip
- Node.js 16+ with npm
- Ollama installed locally
- Git for repository access

### **Installation Steps**

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/restaurant-booking-chat-agent.git
   cd restaurant-booking-chat-agent
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Start Ollama Service**
   ```bash
   ollama serve
   ollama pull llama3.1:8b
   ```

5. **Clone and Launch the Mock API Server (Enhanced fork — 4 restaurants)**
   Repository: [Nikitich2033/Restaurant-Booking-Mock-API-Server](https://github.com/Nikitich2033/Restaurant-Booking-Mock-API-Server)
   ```bash
   # From your workspace root (or a sibling directory)
   git clone https://github.com/Nikitich2033/Restaurant-Booking-Mock-API-Server.git
   cd Restaurant-Booking-Mock-API-Server
   pip install -r requirements.txt
   python -m app.main
   # Server runs on http://localhost:8547
   ```

### **Quick Test**
   ```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi, I need a table for 4 people tonight", "session_id": "test"}'
```

## 🏗️ Design Rationale

### **Framework & Technology Choices**

#### **LangGraph Framework**
- **Why LangGraph**: Chosen for its state-driven conversation management and production-ready architecture
- **Benefits**: 
  - Built-in state persistence and conversation flow control
  - Native async support for high-performance API handling
  - Graph-based workflow that's easy to debug and extend
  - Enterprise-grade error handling and retry mechanisms

#### **Ollama Integration**
- **Why Ollama**: Selected for local LLM processing to ensure data privacy and reduce latency
- **Benefits**:
  - No external API dependencies or rate limits
  - Complete data sovereignty for sensitive booking information
  - Cost-effective for production deployments
  - Customizable model selection (llama3.1:8b for optimal performance)

#### **FastAPI Backend**
- **Why FastAPI**: Chosen for its high performance and automatic API documentation
- **Benefits**:
  - Async-first architecture for concurrent booking requests
  - Automatic OpenAPI/Swagger documentation
  - Built-in validation and error handling
  - Excellent performance for real-time chat applications

### **Design Decisions & Trade-offs**

#### **State Management Strategy**
- **Decision**: Implemented TypedDict with add_messages reducer for conversation state
- **Trade-off**: More complex initial setup vs. robust conversation tracking
- **Rationale**: Long conversations require sophisticated state management that simple session storage cannot provide

#### **Intent Extraction Approach**
- **Decision**: Priority-based regex pattern matching over ML-based classification
- **Trade-off**: Less flexible than ML but more predictable and faster
- **Rationale**: Booking intents are well-defined and pattern-based, making regex more reliable for production use

#### **Database Integration Method**
- **Decision**: Direct SQLAlchemy queries over API abstraction layers
- **Trade-off**: Tighter coupling vs. better performance and real-time data access
- **Rationale**: Restaurant availability requires real-time data that abstraction layers can delay

### **Scalability Architecture**

#### **Horizontal Scaling**
- **Stateless Design**: Each request is independent, allowing multiple server instances
- **Load Balancing**: FastAPI supports multiple worker processes with uvicorn
- **Database Scaling**: SQLite can be replaced with PostgreSQL/MySQL for high-volume deployments

#### **Performance Optimizations**
- **Connection Pooling**: HTTPX client maintains connection pools for external API calls
- **Async Processing**: Non-blocking I/O for concurrent booking operations
- **Context Window Management**: Intelligent conversation pruning for long sessions

#### **Production Deployment**
- **Containerization**: Docker support for consistent deployment environments
- **Environment Configuration**: Configurable settings for different deployment stages
- **Health Monitoring**: Built-in health check endpoints for load balancer integration

### **Identified Limitations & Improvements**

#### **Current Limitations**
1. **Single LLM Provider**: Only Ollama support limits deployment flexibility
2. **Local Model Dependency**: Requires local Ollama installation
3. **Fixed Context Window**: Maximum 60-message conversation history
4. **Limited Multi-language Support**: English-only conversation handling

#### **Planned Improvements**
1. **Multi-LLM Support**: Add OpenAI, Anthropic, and other providers
2. **Cloud Deployment**: Container orchestration with Kubernetes
3. **Advanced Analytics**: Booking pattern analysis and optimization
4. **Multi-language Support**: Internationalization for global deployments
5. **Real-time Notifications**: WebSocket support for live updates

### **Security Considerations & Implementation**

#### **Data Protection**
- **Input Validation**: Comprehensive validation of all user inputs
- **SQL Injection Prevention**: Parameterized queries with SQLAlchemy
- **XSS Protection**: Content sanitization in chat responses
- **Rate Limiting**: Built-in request throttling to prevent abuse

#### **Authentication & Authorization**
- **Session Management**: Secure session handling with unique session IDs
- **API Security**: CORS configuration for controlled cross-origin access
- **Input Sanitization**: Regex pattern validation for booking references

#### **Production Security**
- **HTTPS Enforcement**: TLS/SSL encryption for all communications
- **Environment Variables**: Secure configuration management
- **Audit Logging**: Comprehensive logging of all booking operations

## 📊 Technical Specifications

### **System Requirements**
- **Backend**: Python 3.8+
- **Frontend**: Modern browser with ES6+ support
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **LLM**: Ollama with llama3.1:8b model


### **API Endpoints**
- `POST /chat` - Main conversation endpoint
- `GET /health` - System health check
- `GET /graph-structure` - LangGraph workflow visualization
- `GET /` - Service information

## 🔗 Repository Information

- **Source Code**: [GitHub Repository](https://github.com/your-username/restaurant-booking-chat-agent)
- **Mock API Server (Enhanced fork — 4 restaurants)**: [Nikitich2033/Restaurant-Booking-Mock-API-Server](https://github.com/Nikitich2033/Restaurant-Booking-Mock-API-Server)
- **Documentation**: Comprehensive setup guides and API documentation
- **Testing**: Automated test suites for all user stories and edge cases


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

