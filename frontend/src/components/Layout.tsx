import { Activity, Bell, Cpu, LayoutDashboard, LogOut, SlidersHorizontal } from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [activeAlerts, setActiveAlerts] = useState(0)

  useEffect(() => {
    function fetchCount() {
      api.get('/alerts')
        .then((r) => setActiveAlerts(r.data.filter((a: any) => a.status === 'active').length))
        .catch(() => {})
    }
    fetchCount()
    const id = setInterval(fetchCount, 30000)
    return () => clearInterval(id)
  }, [])

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const NAV = [
    { to: '/',            icon: LayoutDashboard,  label: 'Dashboard',   badge: 0            },
    { to: '/devices',     icon: Cpu,               label: 'Devices',     badge: 0            },
    { to: '/alert-rules', icon: SlidersHorizontal, label: 'Alert Rules', badge: 0            },
    { to: '/alerts',      icon: Bell,              label: 'Alerts',      badge: activeAlerts },
  ]

  return (
    <div className="flex h-screen bg-slate-900 text-slate-100">
      {/* Sidebar */}
      <aside className="w-56 bg-slate-800 flex flex-col shrink-0">
        <div className="flex items-center gap-2 px-4 py-5 border-b border-slate-700">
          <Activity className="text-blue-400" size={20} />
          <span className="font-semibold text-white text-sm">IoT Monitor</span>
        </div>

        <nav className="flex-1 px-2 py-4 space-y-1">
          {NAV.map(({ to, icon: Icon, label, badge }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:bg-slate-700 hover:text-white'
                }`
              }
            >
              <Icon size={16} />
              <span className="flex-1">{label}</span>
              {badge > 0 && (
                <span className="bg-red-500 text-white text-xs font-medium rounded-full px-1.5 py-0.5 min-w-[20px] text-center leading-tight">
                  {badge}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-slate-700">
          <p className="text-xs text-slate-400 truncate">{user?.email}</p>
          <p className="text-xs text-slate-500 capitalize mb-3">{user?.role}</p>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors"
          >
            <LogOut size={14} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
