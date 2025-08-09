# Restaurant Booking Chat Frontend

A modern React + TypeScript frontend for the restaurant booking chat interface, built with Vite.

## Features

- 💬 **Interactive Chat Interface** - Real-time conversation with booking assistant
- 📱 **Responsive Design** - Works seamlessly on desktop and mobile devices
- 🎨 **Modern UI** - Beautiful interface with Tailwind CSS styling
- ⚡ **Fast Performance** - Built with Vite for optimal loading times
- 🔌 **API Integration** - Connects to restaurant booking backend
- 🎯 **Smart Intent Recognition** - Understands natural language booking requests

## Tech Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icon library
- **Axios** - HTTP client for API calls
- **date-fns** - Date utility library

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn

### Installation

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure:
   ```env
   VITE_API_BASE_URL=http://localhost:8547
   VITE_BEARER_TOKEN=your_bearer_token_here
   VITE_RESTAURANT_NAME=TheHungryUnicorn
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Build for production**
   ```bash
   npm run build
   ```

## Project Structure

```
src/
├── components/          # React components
│   ├── Header.tsx      # App header
│   ├── ChatInterface.tsx # Main chat interface
│   ├── MessageBubble.tsx # Individual message component
│   ├── QuickActions.tsx  # Quick action buttons
│   └── BookingCard.tsx   # Booking confirmation card
├── services/           # API and business logic
│   ├── api.ts         # Backend API integration
│   └── chatService.ts # Chat logic and intent processing
├── types/             # TypeScript type definitions
│   └── booking.ts     # Booking-related types
├── App.tsx           # Main app component
├── App.css          # Global styles
├── index.css        # Tailwind CSS imports
└── main.tsx         # React app entry point
```

## Features

### Chat Interface
- Real-time messaging with typing indicators
- Message history with timestamps
- Quick action buttons for common requests
- Auto-scrolling to latest messages

### Booking Management
- Check table availability
- Make new reservations
- View booking confirmations
- Modify or cancel existing bookings
- Booking reference lookup

### Smart Responses
The chat service includes intelligent intent recognition for:
- Availability queries
- Booking requests
- Reservation modifications
- Information requests
- Greeting handling

### API Integration
- RESTful API client with error handling
- Bearer token authentication
- URL-encoded form data support
- Request/response interceptors
- Timeout and retry logic

## Usage Examples

### Check Availability
```
User: "Can you show me availability for this weekend?"
Bot: Shows available time slots with tables
```

### Make Reservation
```
User: "Book a table for 4 people this Friday at 7 PM"
Bot: Finds availability and requests contact details
```

### Modify Booking
```
User: "I need to change my reservation from 6pm to 8pm"
Bot: Requests booking reference and processes modification
```

## Configuration

### Environment Variables
- `VITE_API_BASE_URL` - Backend API base URL
- `VITE_BEARER_TOKEN` - Authentication token
- `VITE_RESTAURANT_NAME` - Restaurant identifier
- `VITE_DEBUG` - Enable debug mode

### Styling
- Tailwind CSS for responsive design
- Custom animations and transitions
- Consistent color scheme
- Mobile-first approach

## Development

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Adding New Features
1. Create components in `src/components/`
2. Add API methods in `src/services/api.ts`
3. Update types in `src/types/booking.ts`
4. Enhance chat logic in `src/services/chatService.ts`

### Testing
```bash
npm run test
```

## Deployment

### Production Build
```bash
npm run build
```

The build artifacts will be in the `dist/` directory.

### Environment Setup
Ensure production environment variables are set:
- Backend API URL
- Production bearer token
- Any required configuration

## Contributing

1. Follow TypeScript best practices
2. Use proper typing for all data
3. Follow component structure patterns
4. Add proper error handling
5. Test on multiple devices

## License

MIT License - see LICENSE file for details