interface BookingCardProps {
  booking: {
    date: string
    time: string
    party: number
    table?: string
    duration?: string
    reference?: string
  }
}

const BookingCard = ({ booking }: BookingCardProps) => {
  return (
    <div className="booking-card">
      <div className="booking-header">
        <h3>🎉 Reservation Confirmed!</h3>
      </div>
      
      <div className="booking-details">
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
      
      <div className="booking-actions">
        <button className="action-btn primary">Confirm Booking</button>
        <button className="action-btn secondary">Modify</button>
      </div>
    </div>
  )
}

export default BookingCard