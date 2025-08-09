import axios from 'axios'
import { Booking, BookingRequest, AvailabilityRequest, ApiResponse, AvailabilitySlot } from '../types/booking'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8547'
const BEARER_TOKEN = import.meta.env.VITE_BEARER_TOKEN || 'your_bearer_token_here'
const RESTAURANT_NAME = 'TheHungryUnicorn'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Authorization': `Bearer ${BEARER_TOKEN}`,
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  timeout: 10000, // 10 seconds
})

// Request interceptor to convert data to URL-encoded format
apiClient.interceptors.request.use((config) => {
  if (config.data && config.headers['Content-Type'] === 'application/x-www-form-urlencoded') {
    const params = new URLSearchParams()
    for (const [key, value] of Object.entries(config.data)) {
      params.append(key, String(value))
    }
    config.data = params
  }
  return config
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    if (error.code === 'ECONNABORTED') {
      throw new Error('Request timeout - please try again')
    }
    if (error.response?.status === 401) {
      throw new Error('Authentication failed - please check your credentials')
    }
    if (error.response?.status >= 500) {
      throw new Error('Server error - please try again later')
    }
    throw error
  }
)

export const bookingApi = {
  // Check availability
  async checkAvailability(request: AvailabilityRequest): Promise<ApiResponse<AvailabilitySlot[]>> {
    try {
      const response = await apiClient.get('/availability', {
        params: {
          restaurant: RESTAURANT_NAME,
          date: request.date,
          time: request.time,
          party: request.party,
        }
      })
      
      return {
        success: true,
        data: response.data,
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to check availability',
      }
    }
  },

  // Create booking
  async createBooking(request: BookingRequest): Promise<ApiResponse<Booking>> {
    try {
      const response = await apiClient.post('/booking', {
        restaurant: RESTAURANT_NAME,
        date: request.date,
        time: request.time,
        party: request.party,
        name: request.name,
        email: request.email,
        phone: request.phone,
        specialRequests: request.specialRequests,
      })
      
      return {
        success: true,
        data: response.data,
        message: 'Booking created successfully',
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to create booking',
      }
    }
  },

  // Get booking by ID
  async getBooking(bookingId: string): Promise<ApiResponse<Booking>> {
    try {
      const response = await apiClient.get(`/booking/${bookingId}`)
      
      return {
        success: true,
        data: response.data,
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Booking not found',
      }
    }
  },

  // Update booking
  async updateBooking(bookingId: string, updates: Partial<BookingRequest>): Promise<ApiResponse<Booking>> {
    try {
      const response = await apiClient.put(`/booking/${bookingId}`, {
        restaurant: RESTAURANT_NAME,
        ...updates,
      })
      
      return {
        success: true,
        data: response.data,
        message: 'Booking updated successfully',
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to update booking',
      }
    }
  },

  // Cancel booking
  async cancelBooking(bookingId: string): Promise<ApiResponse<void>> {
    try {
      await apiClient.delete(`/booking/${bookingId}`)
      
      return {
        success: true,
        message: 'Booking cancelled successfully',
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to cancel booking',
      }
    }
  },
}

export default bookingApi
