import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useAppSelector } from './hooks/useStore'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import LiveFeed from './pages/LiveFeed'
import EventLog from './pages/EventLog'
import ThreatMap from './pages/ThreatMap'
import Models from './pages/Models'

function ProtectedLayout() {
  const isAuthenticated = useAppSelector((s) => s.auth.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <Outlet />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/live" element={<LiveFeed />} />
        <Route path="/events" element={<EventLog />} />
        <Route path="/threats" element={<ThreatMap />} />
        <Route path="/models" element={<Models />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
