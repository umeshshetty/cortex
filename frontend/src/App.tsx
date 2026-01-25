import { useState } from 'react';
import { ProfileCard } from './components/ProfileCard';
import { NoteInput } from './components/NoteInput';
import { MemoryStream } from './components/MemoryStream';
import { Architecture } from './components/Architecture';
import './App.css';

type View = 'dashboard' | 'architecture';

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [view, setView] = useState<View>('dashboard');

  function handleNoteAdded() {
    setRefreshTrigger(prev => prev + 1);
  }

  return (
    <div className="app">
      {/* Background Effects */}
      <div className="bg-gradient" />
      <div className="bg-grid" />

      {/* Header */}
      <header className="header">
        <div className="header-logo">
          <span className="logo-icon">🧠</span>
          <span className="logo-text">Cortex</span>
        </div>
        <nav className="header-nav" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <button
            onClick={() => setView('dashboard')}
            className={`nav-btn ${view === 'dashboard' ? 'active' : ''}`}
            style={{
              background: 'transparent',
              border: 'none',
              color: view === 'dashboard' ? '#fff' : 'rgba(255,255,255,0.6)',
              cursor: 'pointer',
              fontWeight: 500
            }}
          >
            Dashboard
          </button>
          <button
            onClick={() => setView('architecture')}
            className={`nav-btn ${view === 'architecture' ? 'active' : ''}`}
            style={{
              background: 'transparent',
              border: 'none',
              color: view === 'architecture' ? '#fff' : 'rgba(255,255,255,0.6)',
              cursor: 'pointer',
              fontWeight: 500
            }}
          >
            Architecture
          </button>
          <span className="nav-separator" style={{ color: 'rgba(255,255,255,0.2)' }}>|</span>
          <span className="nav-status">
            <span className="status-dot" />
            System Active
          </span>
        </nav>
      </header>

      {/* Main Content */}
      <main className="main">
        {view === 'dashboard' ? (
          <div className="dashboard animate-fade-in">
            {/* Left Column - Profile & Input */}
            <div className="dashboard-left">
              <ProfileCard />
              <NoteInput onNoteAdded={handleNoteAdded} />
            </div>

            {/* Right Column - Memory Stream */}
            <div className="dashboard-right">
              <MemoryStream refreshTrigger={refreshTrigger} />
            </div>
          </div>
        ) : (
          <Architecture />
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <span>Cortex v2.0</span>
        <span>•</span>
        <span>Your Personal Cognitive Assistant</span>
      </footer>
    </div>
  );
}

export default App;
