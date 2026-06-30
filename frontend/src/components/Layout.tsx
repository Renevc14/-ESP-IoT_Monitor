import { Activity, BarChart3, Bell, Cpu, HeartPulse, LayoutDashboard, LogOut, Menu, ScrollText, SlidersHorizontal, Users } from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { cn } from './ui/cn'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [activeAlerts, setActiveAlerts] = useState(0)
  const [navOpen, setNavOpen] = useState(false)

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
    { to: '/',            icon: LayoutDashboard,   label: 'Dashboard',   badge: 0            },
    { to: '/devices',     icon: Cpu,               label: 'Devices',     badge: 0            },
    { to: '/alert-rules', icon: SlidersHorizontal, label: 'Alert Rules', badge: 0            },
    { to: '/alerts',      icon: Bell,              label: 'Alerts',      badge: activeAlerts },
    { to: '/analytics',   icon: BarChart3,         label: 'Analytics',   badge: 0            },
    { to: '/health',      icon: HeartPulse,        label: 'Salud',       badge: 0            },
    ...(user?.role === 'admin'
      ? [
          { to: '/users', icon: Users, label: 'Users', badge: 0 },
          { to: '/logs', icon: ScrollText, label: 'Logs', badge: 0 },
        ]
      : []),
  ]

  const initial = (user?.full_name || user?.email || '?').charAt(0).toUpperCase()

  return (
    <div className="flex h-screen bg-background text-foreground">
      {navOpen && <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={() => setNavOpen(false)} />}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed lg:static inset-y-0 left-0 z-40 w-60 shrink-0 flex flex-col border-r border-line bg-surface transition-transform duration-200',
          navOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        )}
      >
        <div className="flex items-center gap-2.5 px-5 h-16 border-b border-line">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/15 text-accent">
            <Activity size={18} />
          </div>
          <div className="leading-tight">
            <p className="text-sm font-semibold text-foreground">IoT Monitor</p>
            <p className="text-[11px] text-faint">Plataforma de monitoreo</p>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {NAV.map(({ to, icon: Icon, label, badge }) => (
            <NavLink key={to} to={to} end={to === '/'} onClick={() => setNavOpen(false)}>
              {({ isActive }) => (
                <span
                  className={cn(
                    'group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                    isActive ? 'bg-surface-2 text-foreground' : 'text-muted hover:text-foreground hover:bg-surface-2/60',
                  )}
                >
                  {isActive && <span className="absolute left-0 top-2 bottom-2 w-0.5 rounded-full bg-accent" />}
                  <Icon size={17} className={isActive ? 'text-accent' : 'text-faint group-hover:text-muted'} />
                  <span className="flex-1">{label}</span>
                  {badge > 0 && (
                    <span className="rounded-full bg-danger/20 text-danger text-[11px] font-semibold px-1.5 py-0.5 min-w-[20px] text-center leading-tight tnum">
                      {badge}
                    </span>
                  )}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-line px-3 py-3">
          <div className="flex items-center gap-3 px-2 py-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/15 text-accent text-sm font-semibold">
              {initial}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-foreground truncate">{user?.email}</p>
              <p className="text-[11px] text-faint capitalize">{user?.role}</p>
            </div>
            <button onClick={handleLogout} title="Cerrar sesión" className="text-faint hover:text-danger transition-colors p-1.5 rounded-lg hover:bg-surface-2">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="lg:hidden flex items-center gap-3 h-14 border-b border-line bg-surface px-4">
          <button onClick={() => setNavOpen(true)} className="text-muted hover:text-foreground">
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-2">
            <Activity className="text-accent" size={18} />
            <span className="font-semibold text-sm">IoT Monitor</span>
          </div>
        </header>

        <main className="flex-1 overflow-auto">
          <div key={location.pathname} className="mx-auto max-w-[1400px] px-4 sm:px-8 py-6 animate-fade-up">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
