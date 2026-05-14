import {
  BarChart3,
  Bell,
  BookOpen,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Plus,
  Search,
  Settings,
  SlidersHorizontal,
  UserCircle,
} from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/analyze', label: 'Analyze', icon: Search },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/lime', label: 'LIME Deep-Dive', icon: SlidersHorizontal },
  { to: '/rag', label: 'RAG Evidence', icon: ClipboardList },
]

export function AppShell() {
  return (
    <div className="app-frame">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">
            <BarChart3 size={20} />
          </div>
          <div>
            <strong>VerityXAI</strong>
            <span>Analytical Engine</span>
          </div>
        </div>
        <NavLink to="/analyze" className="new-analysis">
          <Plus size={16} />
          New Analysis
        </NavLink>
        <nav className="nav-list" aria-label="Primary navigation">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink key={item.to} to={item.to}>
                <Icon size={17} />
                {item.label}
              </NavLink>
            )
          })}
        </nav>
        <div className="sidebar-footer">
          <button type="button">
            <BookOpen size={16} />
            Docs
          </button>
          <button type="button">
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <h1>VerityXAI</h1>
          <div className="topbar-actions" aria-label="Account tools">
            <button type="button" aria-label="Settings">
              <Settings size={18} />
            </button>
            <button type="button" aria-label="Notifications">
              <Bell size={18} />
            </button>
            <button type="button" aria-label="User profile">
              <UserCircle size={19} />
            </button>
          </div>
        </header>
        <main>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
