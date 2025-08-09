import { User, Bot } from 'lucide-react'
import { format } from 'date-fns'
import { Message } from './ChatInterface'

interface MessageBubbleProps {
  message: Message
}

const MessageBubble = ({ message }: MessageBubbleProps) => {
  const isUser = message.type === 'user'
  
  return (
    <div className={`flex items-start space-x-3 message ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-green-600' : 'bg-blue-600'
      }`}>
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>
      
      {/* Message Content */}
      <div className={`max-w-xs sm:max-w-md lg:max-w-lg xl:max-w-xl ${isUser ? 'text-right' : ''}`}>
        <div className={`rounded-2xl px-4 py-3 ${
          isUser 
            ? 'bg-green-600 text-white' 
            : 'bg-gray-100 text-gray-800'
        }`}>
          <div className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
          </div>
        </div>
        
        {/* Timestamp */}
        <div className={`text-xs text-gray-500 mt-1 ${isUser ? 'text-right' : ''}`}>
          {format(message.timestamp, 'h:mm a')}
        </div>
      </div>
    </div>
  )
}

export default MessageBubble
