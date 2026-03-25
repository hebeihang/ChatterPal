import { useState } from 'react'
import ChatInterface from './components/ChatInterface.tsx'
import PronunciationCorrection from './components/PronunciationCorrection.tsx'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'pronunciation'>('chat')

  return (
    <div className="app">
      <header className="app-header">
        <h1>ChatterPal - 日本語学習パートナー</h1>
        <nav className="tab-nav">
          <button 
            className={`tab-button ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            会話練習
          </button>
          <button 
            className={`tab-button ${activeTab === 'pronunciation' ? 'active' : ''}`}
            onClick={() => setActiveTab('pronunciation')}
          >
            発音矯正
          </button>
        </nav>
      </header>
      
      <main className="app-main">
        {activeTab === 'chat' && <ChatInterface />}
        {activeTab === 'pronunciation' && <PronunciationCorrection />}
      </main>
    </div>
  )
}

export default App