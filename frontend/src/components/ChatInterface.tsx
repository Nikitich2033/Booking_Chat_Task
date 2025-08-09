import { useState, useRef, useEffect } from 'react'
import BookingCard from './BookingCard'
import QuickActions from './QuickActions'
import { chatService } from '../services/chatService'

export interface Message {
  id: string
  type: 'user' | 'bot'
  content: string
  timestamp: Date
  bookingData?: any
  availabilityData?: any
}

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content: "Hello! Welcome to TableBooker! 🍽️ I'm your personal booking assistant for restaurants. How can I help you today?",
      timestamp: new Date(),
    }
  ])
  
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    // Process message with real API integration
    try {
      const botResponse = await chatService.processMessage(userMessage.content)
      setMessages(prev => [...prev, botResponse])
    } catch (error) {
      console.error('Error processing message:', error)
      const errorResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorResponse])
    } finally {
      setIsTyping(false)
    }
  }



  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleQuickAction = (action: string) => {
    setInputValue(action)
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Chat with our Booking Assistant</h2>
      </div>
      
      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id}>
            <div className={`message ${message.type}`}>
              <div className="message-content">
                {message.content}
              </div>
              <div className="message-time">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
            {message.bookingData && (
              <div className="booking-card-container">
                <BookingCard booking={message.bookingData} />
              </div>
            )}
          </div>
        ))}
        
        {isTyping && (
          <div className="message bot">
            <div className="message-content typing">
              Bot is typing...
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <QuickActions onActionClick={handleQuickAction} />

      <div className="input-container">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message here..."
          className="message-input"
        />
        <button
          onClick={handleSendMessage}
          disabled={!inputValue.trim() || isTyping}
          className="send-button"
        >
          Send
        </button>
      </div>
    </div>
  )
}

export default ChatInterface