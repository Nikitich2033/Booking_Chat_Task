import { useState, useRef, useEffect } from 'react'
import BookingCard from './BookingCard'
import QuickActions from './QuickActions'

export interface Message {
  id: string
  type: 'user' | 'bot'
  content: string
  timestamp: Date
  bookingData?: any
}

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content: "Hello! Welcome to TheHungryUnicorn. I'm your personal booking assistant. How can I help you today?",
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

    // Simulate bot response
    setTimeout(() => {
      const responseData = generateResponse(userMessage.content)
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: responseData.content,
        timestamp: new Date(),
        bookingData: responseData.bookingData,
      }
      setMessages(prev => [...prev, botResponse])
      setIsTyping(false)
    }, 1000 + Math.random() * 2000)
  }

  const generateResponse = (userInput: string): { content: string; bookingData?: any } => {
    const input = userInput.toLowerCase()
    
    if (input.includes('availability') || input.includes('available') || input.includes('weekend')) {
      if (input.includes('weekend') || input.includes('friday') || input.includes('saturday')) {
        return {
          content: "Great! I found availability for this weekend:\n\n📅 Friday:\n• 6:00 PM - Available\n• 7:00 PM - Available\n• 8:00 PM - Available\n\n📅 Saturday:\n• 6:30 PM - Available\n• 7:30 PM - Available\n• 8:30 PM - Available\n\nWould you like me to book one of these times for you?"
        }
      }
      return {
        content: "I'd be happy to check availability for you! Could you please tell me:\n\n📅 What date would you like to dine?\n🕐 What time do you prefer?\n👥 How many people will be in your party?\n\nFor example: 'Check availability for 4 people this Friday at 7 PM'"
      }
    } else if (input.includes('book') || input.includes('reserve') || input.includes('table')) {
      if (input.includes('4 people') || input.includes('friday') || input.includes('7')) {
        const bookingData = {
          date: 'Friday, January 26, 2025',
          time: '7:00 PM',
          party: 4,
          table: 'Table 12',
          duration: '2 hours',
          reference: 'BK' + Math.random().toString(36).substr(2, 8).toUpperCase()
        }
        return {
          content: "Perfect! I've found availability and prepared your reservation details:",
          bookingData
        }
      }
      return {
        content: "I'd love to help you make a reservation! To book a table, I'll need:\n\n📅 Your preferred date\n🕐 Your preferred time\n👥 Number of guests\n\nWhat works best for you?"
      }
    } else if (input.includes('modify') || input.includes('change') || input.includes('cancel')) {
      return {
        content: "I can help you modify or cancel your reservation. Please provide:\n\n🔍 Your booking reference number\n📧 Email address used for booking\n\nWhat changes would you like to make?"
      }
    } else if (input.includes('find') || input.includes('check my') || input.includes('existing')) {
      return {
        content: "I can help you find your reservation! Please provide:\n\n🔍 Your booking reference number (e.g., BK12345678)\n   OR\n📧 The email address used for the booking"
      }
    } else if (input.includes('menu') || input.includes('food')) {
      return {
        content: "Our menu features modern European cuisine with seasonal ingredients:\n\n🍽️ Contemporary European dishes\n🥗 Vegetarian and vegan options\n🌾 Gluten-free alternatives\n🍷 Curated wine selection\n\nWould you like me to help you make a reservation?"
      }
    } else if (input.includes('hello') || input.includes('hi') || input.includes('hey')) {
      return {
        content: "Hello! Welcome to TheHungryUnicorn! 🦄✨\n\nI'm your personal dining assistant, ready to help you with:\n\n📅 Checking table availability\n🍽️ Making new reservations\n📋 Managing existing bookings\n❓ Answering restaurant questions\n\nWhat can I help you with today?"
      }
    } else {
      return {
        content: "I'm here to help you with your dining experience at TheHungryUnicorn! 🦄\n\nI can assist you with:\n\n🔍 Checking table availability\n📝 Making new reservations\n📋 Looking up existing bookings\n✏️ Modifying or canceling reservations\n❓ Answering questions about our restaurant\n\nWhat would you like to do today?"
      }
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