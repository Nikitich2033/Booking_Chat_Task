import axios from 'axios'
import type { Booking, BookingRequest, AvailabilityRequest, AvailabilitySlot } from '../types/booking'

interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
const BEARER_TOKEN = import.meta.env.VITE_BEARER_TOKEN || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFwcGVsbGErYXBpQHJlc2RpYXJ5LmNvbSIsIm5iZiI6MTc1NDQzMDgwNSwiZXhwIjoxNzU0NTE3MjA1LCJpYXQiOjE3NTQ0MzA4MDUsImlzcyI6IlNlbGYiLCJhdWQiOiJodHRwczovL2FwaS5yZXNkaWFyeS5jb20ifQ.g3yLsufdk8Fn2094SB3J3XW-KdBc0DY9a2Jiu_56ud8'
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
  // Get available restaurants
  async getRestaurants(): Promise<ApiResponse<{id: number, name: string, microsite_name: string}[]>> {
    try {
      console.log('🏢 Getting list of available restaurants')
      
      // Note: This would require a new API endpoint in the mock server
      // For now, we'll return the known restaurant(s)
      const restaurants = [
        { id: 1, name: 'TheHungryUnicorn', microsite_name: 'TheHungryUnicorn' }
      ]
      
      console.log('✅ Restaurants retrieved:', restaurants)
      
      return {
        success: true,
        data: restaurants
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to get restaurants'
      }
    }
  },
  // Check availability
  async checkAvailability(restaurantName: string, request: AvailabilityRequest): Promise<ApiResponse<AvailabilitySlot[]>> {
    try {
      const requestData = {
        VisitDate: request.date,
        PartySize: request.party.toString(),
        ChannelCode: 'ONLINE'
      }

      console.log('🔍 Checking availability with request:', requestData)

      const response = await apiClient.post(
        `/api/ConsumerApi/v1/Restaurant/${RESTAURANT_NAME}/AvailabilitySearch`,
        requestData
      )
      
      console.log('✅ Availability check successful:', {
        status: response.status,
        data: response.data
      })
      
      // Transform the API response to match our interface
      const availabilitySlots: AvailabilitySlot[] = response.data.available_slots?.map((slot: any) => ({
        time: slot.time,
        available: slot.available,
        table: slot.max_party_size ? `Max ${slot.max_party_size} people` : undefined
      })) || []
      
      console.log('🎯 Transformed availability slots:', availabilitySlots)
      
      return {
        success: true,
        data: availabilitySlots,
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
      const requestData: any = {
        VisitDate: request.date,
        VisitTime: request.time,
        PartySize: request.party.toString(),
        ChannelCode: 'ONLINE'
      }
      
      if (request.name) {
        const nameParts = request.name.split(' ')
        requestData['Customer[FirstName]'] = nameParts[0]
        if (nameParts.length > 1) {
          requestData['Customer[Surname]'] = nameParts.slice(1).join(' ')
        }
      }
      if (request.email) requestData['Customer[Email]'] = request.email
      if (request.phone) requestData['Customer[Mobile]'] = request.phone
      if (request.specialRequests) requestData['SpecialRequests'] = request.specialRequests

      console.log('📝 Creating booking with request:', requestData)

      const response = await apiClient.post(
        `/api/ConsumerApi/v1/Restaurant/${RESTAURANT_NAME}/BookingWithStripeToken`,
        requestData
      )
      
      console.log('✅ Booking creation successful:', {
        status: response.status,
        data: response.data
      })
      
      // Transform API response to our Booking interface
      const booking: Booking = {
        id: response.data.booking_reference,
        date: response.data.visit_date,
        time: response.data.visit_time,
        party: response.data.party_size,
        name: request.name,
        email: request.email,
        phone: request.phone,
        status: response.data.status,
        reference: response.data.booking_reference,
        specialRequests: request.specialRequests,
        createdAt: new Date(response.data.created_at)
      }
      
      console.log('🎯 Transformed booking data:', booking)
      
      return {
        success: true,
        data: booking,
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
  async getBooking(bookingReference: string): Promise<ApiResponse<Booking>> {
    try {
      console.log('🔍 Getting booking with reference:', bookingReference)

      const response = await apiClient.get(
        `/api/ConsumerApi/v1/Restaurant/${RESTAURANT_NAME}/Booking/${bookingReference}`
      )
      
      console.log('✅ Get booking successful:', {
        status: response.status,
        data: response.data
      })
      
      // Transform API response to our Booking interface
      const booking: Booking = {
        id: response.data.booking_reference,
        date: response.data.visit_date,
        time: response.data.visit_time,
        party: response.data.party_size,
        name: response.data.customer?.first_name ? 
          `${response.data.customer.first_name} ${response.data.customer.surname || ''}`.trim() : '',
        email: response.data.customer?.email || '',
        phone: response.data.customer?.mobile || '',
        status: response.data.status,
        reference: response.data.booking_reference,
        specialRequests: response.data.special_requests,
        createdAt: new Date(response.data.created_at),
        updatedAt: response.data.updated_at ? new Date(response.data.updated_at) : undefined
      }
      
      console.log('🎯 Transformed booking data:', booking)
      
      return {
        success: true,
        data: booking,
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Booking not found',
      }
    }
  },

  // Update booking
  async updateBooking(restaurantName: string, bookingReference: string, updates: Partial<BookingRequest>): Promise<ApiResponse<Booking>> {
    try {
      const requestData: any = {}
      
      if (updates.date) requestData.VisitDate = updates.date
      if (updates.time) requestData.VisitTime = updates.time
      if (updates.party) requestData.PartySize = updates.party.toString()
      if (updates.specialRequests) requestData.SpecialRequests = updates.specialRequests

      console.log('✏️ Updating booking with reference:', bookingReference, 'updates:', requestData)

      const response = await apiClient.patch(
        `/api/ConsumerApi/v1/Restaurant/${restaurantName}/Booking/${bookingReference}`,
        requestData
      )
      
      console.log('✅ Booking update successful:', {
        status: response.status,
        data: response.data
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
  async cancelBooking(restaurantName: string, bookingReference: string, cancellationReasonId: number = 1): Promise<ApiResponse<void>> {
    try {
      const requestData = {
        micrositeName: restaurantName,
        bookingReference: bookingReference,
        cancellationReasonId: cancellationReasonId.toString()
      }

      console.log('❌ Cancelling booking with reference:', bookingReference, 'request:', requestData)

      const response = await apiClient.post(
        `/api/ConsumerApi/v1/Restaurant/${restaurantName}/Booking/${bookingReference}/Cancel`,
        requestData
      )
      
      console.log('✅ Booking cancellation successful:', {
        status: response.status,
        data: response.data
      })
      
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
