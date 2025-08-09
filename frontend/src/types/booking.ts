export interface Booking {
  id?: string
  date: string
  time: string
  party: number
  name: string
  email: string
  phone: string
  table?: string
  duration?: string
  status: 'confirmed' | 'pending' | 'cancelled'
  reference?: string
  specialRequests?: string
  createdAt?: Date
  updatedAt?: Date
}

export interface BookingRequest {
  date: string
  time: string
  party: number
  name: string
  email: string
  phone: string
  specialRequests?: string
}

export interface AvailabilityRequest {
  date: string
  time?: string
  party: number
}

export interface AvailabilitySlot {
  time: string
  available: boolean
  table?: string
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface ChatMessage {
  id: string
  type: 'user' | 'bot'
  content: string
  timestamp: Date
  bookingData?: Partial<Booking>
  availabilityData?: AvailabilitySlot[]
}
