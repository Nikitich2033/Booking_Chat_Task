# TableBooker AI Agent Backend - Ollama Edition

A simple and efficient AI agent system for restaurant booking powered by Ollama local AI models.

## 🌟 Features

### 🤖 Simple AI Agent
- **Ollama Integration**: Local AI models (llama3.1:8b)
- **Natural Conversations**: Multi-turn booking conversations
- **Restaurant Focus**: Specialized for TheHungryUnicorn restaurant
- **Memory**: Session-based conversation history

### 🧠 Local AI Model
- **Ollama**: Local llama3.1:8b model
- **Privacy**: No external API calls required
- **Performance**: GPU acceleration support
- **Offline**: Works without internet connection

### 💾 Simple State Management
- **In-Memory Storage**: Fast session management
- **Conversation History**: Maintains context across messages
- **Auto-cleanup**: Memory management for long sessions

### 🍽️ Restaurant Integration
- **TheHungryUnicorn**: Fine dining, modern European cuisine
- **Booking API**: Full integration with mock restaurant API
- **Natural Language**: Understands booking requests in plain English
- **Real-time**: Live availability and booking management

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Ollama installed and running
- llama3.1:8b model downloaded

### Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Ollama** (in separate terminal)
   ```bash
   ollama serve
   ```

3. **Start the Backend**
   ```bash
   python main.py
   ```

The server will start on `http://localhost:8000`

## 📡 API Endpoints

### Chat
- `POST /chat` - Chat with the AI agent
- `GET /health` - Health check
- `GET /ollama/status` - Check Ollama connection

### Sessions
- `GET /sessions/{session_id}` - Get session info

### System
- `GET /` - API information

## 🧪 Testing

```bash
# Test Ollama connection
curl http://localhost:8000/ollama/status

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I want to make a reservation"}'
```

## 🔧 Configuration

The system is pre-configured for:
- **Restaurant**: TheHungryUnicorn
- **Model**: llama3.1:8b
- **Hours**: Tuesday-Sunday 5:00 PM - 11:00 PM
- **Ollama URL**: http://localhost:11434

## 📁 Project Structure

```
backend/
├── main.py                 # Main FastAPI application
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🤖 AI Behavior

The AI agent is configured to:
- Help with restaurant reservations
- Provide restaurant information
- Check table availability
- Handle booking modifications
- Ask for: date, time, party size, and contact information
- Be friendly, professional, and helpful

## 🐛 Troubleshooting

### Ollama Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Pull model if missing
ollama pull llama3.1:8b
```

### Connection Issues
- Ensure Ollama is running on port 11434
- Check firewall settings
- Verify model is downloaded

## 📈 Performance

- **Response Time**: ~2-5 seconds (depends on hardware)
- **Memory Usage**: ~4-8GB (for llama3.1:8b)
- **GPU Support**: NVIDIA, AMD, or CPU fallback
- **Concurrent Users**: Limited by system resources

## 🔒 Security

- **Local Processing**: All AI processing happens locally
- **No External APIs**: No data sent to external services
- **Session Isolation**: Each conversation is separate
- **Memory Management**: Automatic cleanup of old sessions

---

**Simple, Local, and Efficient** ✨