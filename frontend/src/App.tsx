import React from 'react'
import ChatInterface from './components/ChatInterface'
import './App.css'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>🦄 TheHungryUnicorn</h1>
        <p>Restaurant Booking Assistant</p>
      </header>
      
      <main className="main-content">
        <ChatInterface />
      </main>
    </div>
  )
}

export default App