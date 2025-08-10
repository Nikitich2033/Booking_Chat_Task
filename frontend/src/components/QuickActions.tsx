import { useState } from 'react'

interface QuickActionsProps {
  onActionClick: (action: string) => void
}

const QuickActions = ({ onActionClick }: QuickActionsProps) => {
  const [isVisible, setIsVisible] = useState(true)
  const quickActions = [
    {
      emoji: "📅",
      label: "Check Availability",
      action: "Can you show me availability for this weekend?"
    },
    {
      emoji: "🍽️",
      label: "Book Table",
      action: "I'd like to book a table for 4 people"
    },
    {
      emoji: "🔍",
      label: "Find Booking",
      action: "I need to check my existing reservation"
    },
    {
      emoji: "✏️",
      label: "Modify Booking",
      action: "I need to change my reservation"
    }
  ]

  return (
    <div className="quick-actions">
      <div className="quick-actions-header">
        <div className="quick-actions-label">Quick actions:</div>
        <button
          onClick={() => setIsVisible(!isVisible)}
          className="quick-actions-toggle"
          title={isVisible ? "Hide quick actions" : "Show quick actions"}
        >
          {isVisible ? "🙈" : "👀"} {isVisible ? "Hide" : "Show"}
        </button>
      </div>
      
      {isVisible && (
        <div className="quick-actions-buttons">
          {quickActions.map((action, index) => (
            <button
              key={index}
              onClick={() => onActionClick(action.action)}
              className="quick-action-btn"
              title={action.action}
            >
              <span className="quick-action-emoji">{action.emoji}</span>
              <span className="quick-action-label">{action.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default QuickActions