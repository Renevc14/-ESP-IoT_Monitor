import { ApolloProvider } from '@apollo/client/react'
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import { apolloClient } from './api/apollo'
import Layout from './components/Layout'
import { AuthProvider, useAuth } from './context/AuthContext'
import AlertRules from './pages/AlertRules'
import Alerts from './pages/Alerts'
import Dashboard from './pages/Dashboard'
import Devices from './pages/Devices'
import Login from './pages/Login'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  return user ? <>{children}</> : <Navigate to="/login" replace />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
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
