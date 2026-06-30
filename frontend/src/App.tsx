import { ApolloProvider } from '@apollo/client/react'
import { lazy, Suspense } from 'react'
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import { apolloClient } from './api/apollo'
import Layout from './components/Layout'
import { AuthProvider, useAuth } from './context/AuthContext'
import AlertRules from './pages/AlertRules'
import Alerts from './pages/Alerts'
import Devices from './pages/Devices'
import ForgotPassword from './pages/ForgotPassword'
import Health from './pages/Health'
import Login from './pages/Login'
import Logs from './pages/Logs'
import ResetPassword from './pages/ResetPassword'
import Users from './pages/Users'

// Carga diferida de las páginas con Recharts (el chunk pesado) para sacarlo del
// bundle inicial: solo se descarga al entrar a Dashboard/Analytics.
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Analytics = lazy(() => import('./pages/Analytics'))

const RouteFallback = () => (
  <div className="flex items-center justify-center p-12 text-sm text-muted">Cargando…</div>
)

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
        <Route index element={<Suspense fallback={<RouteFallback />}><Dashboard /></Suspense>} />
        <Route path="devices" element={<Devices />} />
        <Route path="alert-rules" element={<AlertRules />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="analytics" element={<Suspense fallback={<RouteFallback />}><Analytics /></Suspense>} />
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
