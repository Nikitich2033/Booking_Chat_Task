import { CalendarDays, Clock } from 'lucide-react'

const Header = () => {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">🦄</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">TableBooker</h1>
              <p className="text-sm text-gray-600">Multi-Restaurant Booking Platform</p>
            </div>
          </div>
          
          <div className="hidden md:flex items-center space-x-6 text-sm text-gray-600">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4" />
              <span>Open: 5:00 PM - 11:00 PM</span>
            </div>
            <div className="flex items-center space-x-2">
              <CalendarDays className="w-4 h-4" />
              <span>Reservations Available</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
