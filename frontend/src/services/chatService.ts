import type { AvailabilityRequest } from '../types/booking'
import bookingApi from './api'

interface ChatMessage {
  id: string
  type: 'user' | 'bot'
  content: string
  timestamp: Date
  bookingData?: any
  availabilityData?: any
}

interface RestaurantContext {
  selectedRestaurant: string | null
  availableRestaurants: {id: number, name: string, microsite_name: string}[]
}

interface AgentChatRequest {
  message: string
  session_id?: string
  user_id?: string
  context?: Record<string, any>
}

interface AgentChatResponse {
  message: string
  session_id: string
  agent_responses?: Array<{
    agent_type: string
    message: string
    actions_taken: string[]
    next_agent?: string
    booking_data?: any
    requires_user_input: boolean
    confidence_score: number
  }>
  conversation_state?: Record<string, any>
  suggestions?: string[]
  booking_data?: any
  availability_data?: any
  intent?: Record<string, any>
}

export class ChatService {
  private conversationHistory: ChatMessage[] = []
  private sessionId: string | null = null
  private agentApiUrl: string = import.meta.env.VITE_AGENT_API_URL || 'http://localhost:8000'
  private restaurantContext: RestaurantContext = {
    selectedRestaurant: null,
    availableRestaurants: []
  }

  constructor() {
    this.initializeRestaurants()
  }

  private async initializeRestaurants() {
    try {
      const result = await bookingApi.getRestaurants()
      if (result.success && result.data) {
        this.restaurantContext.availableRestaurants = result.data
        // Auto-select if only one restaurant
        if (result.data.length === 1) {
          this.restaurantContext.selectedRestaurant = result.data[0].microsite_name
        }
      }
    } catch (error) {
      console.error('Failed to initialize restaurants:', error)
    }
  }

  async processMessage(userMessage: string): Promise<ChatMessage> {
    // Add user message to history
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: userMessage,
      timestamp: new Date(),
    }
    this.conversationHistory.push(userMsg)

    try {
      // Call the AI agent backend
      const agentResponse = await this.callAgentAPI(userMessage)
      
      // Create bot response from agent
      const confirmedBooking = this.extractBookingData(agentResponse)
      const botResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: agentResponse.message,
        timestamp: new Date(),
        bookingData: confirmedBooking,
        availabilityData: this.extractAvailabilityData(agentResponse)
      }
      
      this.conversationHistory.push(botResponse)
      
      // Update session ID if provided
      if (agentResponse.session_id) {
        this.sessionId = agentResponse.session_id
      }
      
      // Update restaurant context from agent response
      if (agentResponse.conversation_state?.current_restaurant) {
        this.restaurantContext.selectedRestaurant = agentResponse.conversation_state.current_restaurant
      } else if (!this.restaurantContext.selectedRestaurant) {
        // Default to TheHungryUnicorn for simple backend
        this.restaurantContext.selectedRestaurant = 'TheHungryUnicorn'
      }

      return botResponse

    } catch (error) {
      console.error('AI Agent API Error:', error)
      
      // Fallback to local processing if agent API fails
      const fallbackResponse = await this.generateFallbackResponse(userMessage)
      this.conversationHistory.push(fallbackResponse)
      return fallbackResponse
    }
  }

  private async callAgentAPI(message: string): Promise<AgentChatResponse> {
    console.log('🤖 Calling AI Agent API:', { message, sessionId: this.sessionId })
    
    const request: AgentChatRequest = {
      message,
      session_id: this.sessionId || undefined,
      context: {
        current_restaurant: this.restaurantContext.selectedRestaurant
      }
    }

    const response = await fetch(`${this.agentApiUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    })

    if (!response.ok) {
      throw new Error(`Agent API error: ${response.status} ${response.statusText}`)
    }

    const result: AgentChatResponse = await response.json()
    
    console.log('✅ Agent API Response:', result)
    
    return result
  }

  private extractBookingData(agentResponse: AgentChatResponse): any {
    // Only show card for freshly confirmed bookings triggered by a 'book' action
    const action = agentResponse.intent?.action?.toLowerCase?.()
    const bd = agentResponse.booking_data
    const status = typeof bd?.status === 'string' ? bd.status.toLowerCase() : undefined
    if (action === 'book' && status === 'confirmed') {
      return bd
    }

    // Legacy/agent_responses format: still only if action is 'book' and confirmed
    if (agentResponse.agent_responses && Array.isArray(agentResponse.agent_responses)) {
      if (action === 'book') {
        for (const response of agentResponse.agent_responses) {
          const rbd = response.booking_data
          const rstatus = typeof rbd?.status === 'string' ? rbd.status.toLowerCase() : undefined
          if (rbd && rstatus === 'confirmed') {
            return rbd
          }
        }
      }
    }

    // For lookup, update, cancel or any non-confirmed status, don't show a card
    return null
  }

  private extractAvailabilityData(agentResponse: AgentChatResponse): any {
    // Handle direct availability data from Ollama backend
    if (agentResponse.availability_data) {
      return agentResponse.availability_data
    }
    
    // Handle both full AI response and simple response formats (legacy)
    if (agentResponse.agent_responses && Array.isArray(agentResponse.agent_responses)) {
      // Full AI agent response format
      for (const response of agentResponse.agent_responses) {
        if (response.agent_type === 'availability' && response.confidence_score > 0.7) {
          return { available: true, message: response.message }
        }
      }
    }
    // Simple response format - check if message contains availability info
    if (agentResponse.message.toLowerCase().includes('availability')) {
      return { available: true, message: agentResponse.message }
    }
    return null
  }

  private async generateFallbackResponse(userInput: string): Promise<ChatMessage> {
    console.warn('🔄 Using fallback response - AI Agent API unavailable')
    
    const input = userInput.toLowerCase()
    let response = ""

    // Simple fallback responses when AI is unavailable
    if (this.containsIntent(input, ['hello', 'hi', 'hey'])) {
      response = "Hello! I'm having trouble connecting to our AI system right now, but I'm still here to help with basic questions about TableBooker. What can I do for you?"
    }
    else if (this.containsIntent(input, ['book', 'reserve', 'table'])) {
      response = "I'd love to help you make a reservation! Unfortunately, our AI booking system is temporarily unavailable. Please try again in a moment or contact us directly."
    }
    else if (this.containsIntent(input, ['availability', 'available'])) {
      response = "I'd be happy to check availability for you, but our AI system is currently offline. Please try again shortly."
    }
    else {
      response = "I'm sorry, but our AI assistant is temporarily unavailable. Please try again in a few moments. In the meantime, you can contact us directly for immediate assistance."
    }

    return {
      id: (Date.now() + 1).toString(),
      type: 'bot',
      content: response,
      timestamp: new Date(),
    }
  }

  private containsIntent(input: string, keywords: string[]): boolean {
    return keywords.some(keyword => input.includes(keyword))
  }

  private handleRestaurantSelection(input: string) {
    // If only one restaurant available, auto-select it
    if (this.restaurantContext.availableRestaurants.length === 1) {
      this.restaurantContext.selectedRestaurant = this.restaurantContext.availableRestaurants[0].microsite_name
      const restaurant = this.restaurantContext.availableRestaurants[0]
      return {
        response: `Great! I've selected ${restaurant.name} for you. 🍽️\n\nNow, how can I help you with your dining experience? I can assist with:\n\n• Checking table availability\n• Making new reservations\n• Managing existing bookings\n\nWhat would you like to do?`
      }
    }

    // Multiple restaurants - show selection
    if (this.restaurantContext.availableRestaurants.length > 1) {
      const restaurantList = this.restaurantContext.availableRestaurants
        .map((r, index) => `${index + 1}. ${r.name}`)
        .join('\n')
      
      return {
        response: `Welcome to TableBooker! 🍽️\n\nI can help you with reservations at any of these restaurants:\n\n${restaurantList}\n\nWhich restaurant would you like to book at? Just let me know the name or number.`
      }
    }

    // No restaurants available
    return {
      response: "I'm sorry, but there are no restaurants available for booking at the moment. Please try again later."
    }
  }

  private async handleAvailabilityQuery(input: string) {
    // Extract date and party size from input (simplified logic)
    const dateMatch = input.match(/(today|tomorrow|this weekend|friday|saturday|sunday|monday|tuesday|wednesday|thursday)/i)
    const partyMatch = input.match(/(\d+)\s*(people|person|guest)/i)
    
    if (dateMatch && partyMatch) {
      try {
        const party = parseInt(partyMatch[1])
        const dateStr = this.getDateForString(dateMatch[1])
        
        const availabilityRequest: AvailabilityRequest = {
          date: dateStr,
          party: party
        }

        if (!this.restaurantContext.selectedRestaurant) {
          return {
            response: "Please select a restaurant first. Which restaurant would you like to book at?",
            availabilityData: null
          }
        }

        const result = await bookingApi.checkAvailability(this.restaurantContext.selectedRestaurant, availabilityRequest)
        
        if (result.success && result.data) {
          const availableSlots = result.data.filter(slot => slot.available)
          
          if (availableSlots.length > 0) {
            const timesList = availableSlots.map(slot => 
              `• ${this.formatTime(slot.time)} ${slot.table ? `(${slot.table})` : ''}`
            ).join('\n')
            
            return {
              response: `Great news! I found availability for ${party} ${party === 1 ? 'person' : 'people'} on ${this.formatDateForDisplay(dateMatch[1])}:\n\n${timesList}\n\nWould you like me to book one of these times for you?`,
              availabilityData: result.data
            }
          } else {
            return {
              response: `I'm sorry, but we don't have availability for ${party} ${party === 1 ? 'person' : 'people'} on ${this.formatDateForDisplay(dateMatch[1])}. Would you like me to check alternative dates or times?`,
              availabilityData: null
            }
          }
        } else {
          return {
            response: result.error || "I'm having trouble checking availability right now. Please try again or call us directly.",
            availabilityData: null
          }
        }
      } catch (error) {
        return {
          response: "I'm having trouble checking availability right now. Please try again or call us directly.",
          availabilityData: null
        }
      }
    }

    return {
      response: "I'd be happy to check availability for you! Could you please tell me:\n\n📅 What date would you like to dine?\n🕐 What time do you prefer?\n👥 How many people will be in your party?\n\nFor example: 'Check availability for 4 people this Friday at 7 PM'",
      availabilityData: null
    }
  }

  private async handleBookingRequest(input: string) {
    // Extract booking details from input
    const dateMatch = input.match(/(today|tomorrow|this weekend|friday|saturday|sunday|monday|tuesday|wednesday|thursday)/i)
    const timeMatch = input.match(/(\d+):?(\d*)\s*(pm|am|p\.m\.|a\.m\.)/i)
    const partyMatch = input.match(/(\d+)\s*(people|person|guest)/i)

    if (dateMatch && timeMatch && partyMatch) {
      // Generate mock booking confirmation
      const mockBooking = {
        id: 'BK' + Date.now().toString().slice(-6),
        date: this.formatDate(dateMatch[1]),
        time: `${timeMatch[1]}:${timeMatch[2] || '00'} ${timeMatch[3].toUpperCase()}`,
        party: parseInt(partyMatch[1]),
        table: 'Table 12',
        duration: '2 hours',
        status: 'confirmed' as const,
        reference: 'BK' + Math.random().toString(36).substr(2, 8).toUpperCase()
      }

      return {
        response: `Perfect! I've found availability and can book this for you:\n\n📅 ${mockBooking.date}\n🕐 ${mockBooking.time}\n👥 ${mockBooking.party} ${mockBooking.party === 1 ? 'guest' : 'guests'}\n🪑 ${mockBooking.table}\n\nTo complete your reservation, I'll need:\n• Your name\n• Email address\n• Phone number\n\nWould you like to proceed with this booking?`,
        bookingData: mockBooking
      }
    }

    return {
      response: "I'd love to help you make a reservation! To book a table, please tell me:\n\n📅 Your preferred date\n🕐 Your preferred time\n👥 Number of guests\n\nFor example: 'Book a table for 4 people this Friday at 7 PM'",
      bookingData: null
    }
  }

  private async handleBookingModification(input: string): Promise<string> {
    return "I can help you modify or cancel your reservation. Please provide:\n\n🔍 Your booking reference number\n📧 The email address used for the booking\n\nOnce I have this information, I can help you:\n• Change the date or time\n• Modify party size\n• Add special requests\n• Cancel the reservation\n\nWhat would you like to do?"
  }

  private async handleBookingLookup(input: string): Promise<string> {
    return "I can help you find your reservation! Please provide:\n\n🔍 Your booking reference number (e.g., BK12345678)\n   OR\n📧 The email address used for the booking\n\nI'll look up your reservation details and show you all the information."
  }

  private getDateForString(dateString: string): string {
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    switch (dateString.toLowerCase()) {
      case 'today':
        return today.toISOString().split('T')[0] // YYYY-MM-DD format
      case 'tomorrow':
        return tomorrow.toISOString().split('T')[0]
      case 'friday':
        return this.getNextWeekday(5) // Friday is day 5
      case 'saturday':
        return this.getNextWeekday(6)
      case 'sunday':
        return this.getNextWeekday(0)
      case 'monday':
        return this.getNextWeekday(1)
      case 'tuesday':
        return this.getNextWeekday(2)
      case 'wednesday':
        return this.getNextWeekday(3)
      case 'thursday':
        return this.getNextWeekday(4)
      default:
        return today.toISOString().split('T')[0]
    }
  }

  private getNextWeekday(targetDay: number): string {
    const today = new Date()
    const currentDay = today.getDay()
    let daysUntilTarget = targetDay - currentDay
    
    if (daysUntilTarget <= 0) {
      daysUntilTarget += 7 // Next week
    }
    
    const targetDate = new Date(today)
    targetDate.setDate(today.getDate() + daysUntilTarget)
    return targetDate.toISOString().split('T')[0]
  }

  private formatDateForDisplay(dateString: string): string {
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    switch (dateString.toLowerCase()) {
      case 'today':
        return today.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
      case 'tomorrow':
        return tomorrow.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
      default:
        return dateString.charAt(0).toUpperCase() + dateString.slice(1)
    }
  }

  private formatTime(timeString: string): string {
    // Convert 24-hour format to 12-hour format
    const [hours, minutes] = timeString.split(':')
    const hour = parseInt(hours)
    const ampm = hour >= 12 ? 'PM' : 'AM'
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour
    return `${displayHour}:${minutes} ${ampm}`
  }

  private getDefaultResponse(): string {
    const selectedRestaurant = this.restaurantContext.selectedRestaurant 
      ? this.restaurantContext.availableRestaurants.find(r => r.microsite_name === this.restaurantContext.selectedRestaurant)?.name 
      : null

    if (selectedRestaurant) {
      return `I'm here to help you with your dining experience at ${selectedRestaurant}! 🍽️\n\nI can assist you with:\n\n🔍 Checking table availability\n📝 Making new reservations\n📋 Looking up existing bookings\n✏️ Modifying or canceling reservations\n❓ Answering questions about the restaurant\n\nWhat would you like to do today?`
    } else {
      return "Welcome to TableBooker! 🍽️\n\nI'm your dining assistant for multiple restaurants. Please let me know which restaurant you'd like to book at, and I'll help you with:\n\n🔍 Checking table availability\n📝 Making new reservations\n📋 Looking up existing bookings\n✏️ Modifying or canceling reservations\n\nWhich restaurant interests you?"
    }
  }

  getConversationHistory(): ChatMessage[] {
    return [...this.conversationHistory]
  }

  clearHistory(): void {
    this.conversationHistory = []
  }
}

export const chatService = new ChatService()
