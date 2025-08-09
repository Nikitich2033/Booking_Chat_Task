import { ChatMessage } from '../types/booking'
import bookingApi from './api'

export class ChatService {
  private conversationHistory: ChatMessage[] = []

  async processMessage(userMessage: string): Promise<ChatMessage> {
    // Add user message to history
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: userMessage,
      timestamp: new Date(),
    }
    this.conversationHistory.push(userMsg)

    // Process the message and generate response
    const botResponse = await this.generateBotResponse(userMessage)
    this.conversationHistory.push(botResponse)

    return botResponse
  }

  private async generateBotResponse(userInput: string): Promise<ChatMessage> {
    const input = userInput.toLowerCase()
    let response = ""
    let bookingData = null
    let availabilityData = null

    try {
      // Intent detection based on keywords
      if (this.containsIntent(input, ['availability', 'available', 'check', 'free', 'open'])) {
        const { response: resp, availabilityData: avail } = await this.handleAvailabilityQuery(input)
        response = resp
        availabilityData = avail
      } 
      else if (this.containsIntent(input, ['book', 'reserve', 'table', 'reservation'])) {
        const { response: resp, bookingData: booking } = await this.handleBookingRequest(input)
        response = resp
        bookingData = booking
      }
      else if (this.containsIntent(input, ['cancel', 'modify', 'change', 'update'])) {
        response = await this.handleBookingModification(input)
      }
      else if (this.containsIntent(input, ['find', 'lookup', 'reference', 'booking id'])) {
        response = await this.handleBookingLookup(input)
      }
      else if (this.containsIntent(input, ['menu', 'food', 'cuisine', 'dishes'])) {
        response = "Our menu features modern European cuisine with seasonal ingredients. We offer:\n\n🍽️ Contemporary European dishes\n🥗 Vegetarian and vegan options\n🌾 Gluten-free alternatives\n🍷 Curated wine selection\n\nWould you like me to help you make a reservation to experience our culinary offerings?"
      }
      else if (this.containsIntent(input, ['hours', 'open', 'close', 'timing'])) {
        response = "TheHungryUnicorn is open:\n\n🕔 Tuesday - Sunday: 5:00 PM - 11:00 PM\n❌ Closed Mondays\n\nWe accept reservations for dinner service. Would you like to check availability for a specific date?"
      }
      else if (this.containsIntent(input, ['hello', 'hi', 'hey', 'good morning', 'good evening'])) {
        response = "Hello! Welcome to TheHungryUnicorn! 🦄✨\n\nI'm your personal dining assistant, ready to help you with:\n\n• Checking table availability\n• Making new reservations  \n• Managing existing bookings\n• Answering questions about our restaurant\n\nWhat can I help you with today?"
      }
      else {
        response = this.getDefaultResponse()
      }
    } catch (error) {
      console.error('Error processing message:', error)
      response = "I apologize, but I'm experiencing some technical difficulties. Please try again in a moment, or feel free to call us directly for assistance."
    }

    return {
      id: (Date.now() + 1).toString(),
      type: 'bot',
      content: response,
      timestamp: new Date(),
      bookingData,
      availabilityData,
    }
  }

  private containsIntent(input: string, keywords: string[]): boolean {
    return keywords.some(keyword => input.includes(keyword))
  }

  private async handleAvailabilityQuery(input: string) {
    // Extract date and party size from input (simplified logic)
    const dateMatch = input.match(/(today|tomorrow|this weekend|friday|saturday|sunday|monday|tuesday|wednesday|thursday)/i)
    const partyMatch = input.match(/(\d+)\s*(people|person|guest)/i)
    
    if (dateMatch || partyMatch) {
      try {
        // Mock availability check - in production this would call the real API
        const mockAvailability = [
          { time: '5:00 PM', available: true, table: 'Table 12' },
          { time: '6:00 PM', available: true, table: 'Table 8' },
          { time: '7:00 PM', available: false },
          { time: '8:00 PM', available: true, table: 'Table 15' },
          { time: '9:00 PM', available: true, table: 'Table 3' },
        ]

        const date = dateMatch ? dateMatch[1] : 'your requested date'
        const party = partyMatch ? parseInt(partyMatch[1]) : 'your party size'

        const availableSlots = mockAvailability.filter(slot => slot.available)
        
        if (availableSlots.length > 0) {
          const timesList = availableSlots.map(slot => `• ${slot.time} (${slot.table})`).join('\n')
          return {
            response: `Great news! I found availability for ${party} ${party === 1 ? 'person' : 'people'} on ${date}:\n\n${timesList}\n\nWould you like me to book one of these times for you?`,
            availabilityData: mockAvailability
          }
        } else {
          return {
            response: `I'm sorry, but we don't have availability for ${party} ${party === 1 ? 'person' : 'people'} on ${date}. Would you like me to check alternative dates or times?`,
            availabilityData: null
          }
        }
      } catch (error) {
        return {
          response: "I'm having trouble checking availability right now. Please try again or call us directly at (555) 123-4567.",
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

  private formatDate(dateString: string): string {
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    switch (dateString.toLowerCase()) {
      case 'today':
        return today.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
      case 'tomorrow':
        return tomorrow.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
      case 'friday':
        return 'Friday, January 26, 2025'
      case 'saturday':
        return 'Saturday, January 27, 2025'
      case 'sunday':
        return 'Sunday, January 28, 2025'
      default:
        return dateString
    }
  }

  private getDefaultResponse(): string {
    return "I'm here to help you with your dining experience at TheHungryUnicorn! 🦄\n\nI can assist you with:\n\n🔍 Checking table availability\n📝 Making new reservations\n📋 Looking up existing bookings\n✏️ Modifying or canceling reservations\n❓ Answering questions about our restaurant\n\nWhat would you like to do today?"
  }

  getConversationHistory(): ChatMessage[] {
    return [...this.conversationHistory]
  }

  clearHistory(): void {
    this.conversationHistory = []
  }
}

export const chatService = new ChatService()
