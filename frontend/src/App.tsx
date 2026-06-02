import { ApolloProvider } from '@apollo/client/react'
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import { apolloClient } from './api/apollo'
import Layout from './components/Layout'
import { AuthProvider, useAuth } from './context/AuthContext'
import AlertRules from './pages/AlertRules'
import Alerts from './pages/Alerts'
import Analytics from './pages/Analytics'
import Dashboard from './pages/Dashboard'
import Devices from './pages/Devices'
import ForgotPassword from './pages/ForgotPassword'
import Health from './pages/Health'
import Login from './pages/Login'
import Logs from './pages/Logs'
import ResetPassword from './pages/ResetPassword'
import Users from './pages/Users'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  return user ? <>{children}</> : <Navigate to="/login" replace />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="devices" element={<Devices />} />
        <Route path="alert-rules" element={<AlertRules />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="users" element={<Users />} />
        <Route path="logs" element={<Logs />} />
        <Route path="health" element={<Health />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <ApolloProvider client={apolloClient}>
      <AuthProvider>
        <Router>
          <AppRoutes />
        </Router>
      </AuthProvider>
    </ApolloProvider>
  )
}
