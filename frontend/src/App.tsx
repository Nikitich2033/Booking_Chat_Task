import React from 'react'
import ChatInterface from './components/ChatInterface'
import './App.css'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>🍽️ TableBooker</h1>
        <p>Smart Restaurant Reservation Platform</p>
      </header>
      
      <main className="main-content">
        <ChatInterface />
      </main>
    </div>
  )
}

export default App