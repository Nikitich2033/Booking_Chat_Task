interface BookingCardProps {
  booking: {
    date: string
    time: string
    party: number
    table?: string
    duration?: string
    reference?: string
    name?: string
    email?: string
    phone?: string
    restaurant?: string
  }
}

const BookingCard = ({ booking }: BookingCardProps) => {
  return (
    <div className="booking-card">
      <div className="booking-header">
        <h3>🎉 Reservation Confirmed!</h3>
      </div>
      
      <div className="booking-details">
        {booking.restaurant && (
          <div className="booking-row">
            <span className="booking-label">🍽️ Restaurant:</span>
            <span className="booking-value">{booking.restaurant}</span>
          </div>
        )}
        <div className="booking-row">
          <span className="booking-label">📅 Date:</span>
          <span className="booking-value">{booking.date}</span>
        </div>
        
        <div className="booking-row">
          <span className="booking-label">🕐 Time:</span>
          <span className="booking-value">{booking.time}</span>
        </div>
        
        <div className="booking-row">
          <span className="booking-label">👥 Party Size:</span>
          <span className="booking-value">{booking.party} {booking.party === 1 ? 'guest' : 'guests'}</span>
        </div>
        {booking.name && (
          <div className="booking-row">
            <span className="booking-label">👤 Customer:</span>
            <span className="booking-value">{booking.name}</span>
          </div>
        )}
        {booking.email && (
          <div className="booking-row">
            <span className="booking-label">📧 Email:</span>
            <span className="booking-value">{booking.email}</span>
          </div>
        )}
        {booking.phone && (
          <div className="booking-row">
            <span className="booking-label">📱 Phone:</span>
            <span className="booking-value">{booking.phone}</span>
          </div>
        )}
        
        {booking.table && (
          <div className="booking-row">
            <span className="booking-label">🪑 Table:</span>
            <span className="booking-value">{booking.table}</span>
          </div>
        )}
        
        {booking.duration && (
          <div className="booking-row">
            <span className="booking-label">⏱️ Duration:</span>
            <span className="booking-value">{booking.duration}</span>
          </div>
        )}
        
        {booking.reference && (
          <div className="booking-row">
            <span className="booking-label">🔍 Reference:</span>
            <span className="booking-value reference">{booking.reference}</span>
          </div>
        )}
      </div>
      
      {/* actions removed for demo card-only display */}
    </div>
  )
}

export default BookingCard