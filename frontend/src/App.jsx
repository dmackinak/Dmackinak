import { Routes, Route, NavLink } from 'react-router-dom'
import { Scissors, Settings, Film } from 'lucide-react'
import UploadPage from './pages/UploadPage'
import JobPage from './pages/JobPage'
import SettingsPage from './pages/SettingsPage'
import HistoryPage from './pages/HistoryPage'
import './App.css'

export default function App() {
  return (
    <div className="app-shell">
      <nav className="sidebar">
        <div className="logo">
          <Scissors size={22} color="var(--accent)" />
          <span>Shorts<br />Cutter</span>
        </div>
        <div className="nav-links">
          <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
            <Scissors size={18} /> Upload
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
            <Film size={18} /> History
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
            <Settings size={18} /> Settings
          </NavLink>
        </div>
      </nav>
      <main className="content">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/job/:jobId" element={<JobPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  )
}
