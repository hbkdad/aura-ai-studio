import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Revenue from './pages/Revenue'
import Treasury from './pages/Treasury'
import AgentTasks from './pages/AgentTasks'
import WalletSafety from './pages/WalletSafety'
import Settings from './pages/Settings'
import Memory from './pages/Memory'
import './App.css'

const NAV = [
  { to: '/', label: '⬡ Dashboard' },
  { to: '/revenue', label: '$ Revenue' },
  { to: '/treasury', label: '◈ Treasury' },
  { to: '/agents', label: '◉ Agent Tasks' },
  { to: '/wallet', label: '₿ Wallet Safety' },
  { to: '/memory', label: '◈ Memory' },
  { to: '/settings', label: '⚙ Settings' },
]

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-icon">⚡</span>
          <span className="logo-text">AutoSats</span>
          <span className="logo-badge">PAPER</span>
        </div>
        <nav className="sidebar-nav">
          {NAV.map(n => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === '/'}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="mode-badge">PAPER MODE V0.1</span>
        </div>
      </aside>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/revenue" element={<Revenue />} />
          <Route path="/treasury" element={<Treasury />} />
          <Route path="/agents" element={<AgentTasks />} />
          <Route path="/wallet" element={<WalletSafety />} />
          <Route path="/memory" element={<Memory />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
