import { NavLink } from 'react-router-dom'

const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/monitoring', label: 'Monitoring', icon: '🔍' },
    { path: '/alerts', label: 'Alerts', icon: '🔔' },
]

export default function Sidebar() {
    return (
        <aside className="w-64 h-screen bg-black/40 backdrop-blur-2xl border-r border-white/5 flex flex-col shrink-0">
            {/* Logo */}
            <div className="p-6 border-b border-white/5">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-solar-400 to-solar-600 flex items-center justify-center text-xl shadow-lg shadow-solar-500/25">
                        ☀️
                    </div>
                    <div>
                        <h1 className="font-bold text-sm text-white tracking-tight">Solar Intelligence</h1>
                        <p className="text-[10px] text-gray-500 uppercase tracking-widest">Prediction Platform</p>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-1">
                {navItems.map(item => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        end={item.path === '/'}
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${isActive
                                ? 'bg-gradient-to-r from-solar-500/20 to-solar-600/10 text-solar-400 border border-solar-500/20 shadow-lg shadow-solar-500/5'
                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`
                        }
                    >
                        <span className="text-lg">{item.icon}</span>
                        <span>{item.label}</span>
                    </NavLink>
                ))}
            </nav>

            {/* Status Footer */}
            <div className="p-4 border-t border-white/5">
                <div className="glass-card p-3 rounded-xl">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-slow" />
                        <span className="text-xs font-medium text-emerald-400">System Online</span>
                    </div>
                    <p className="text-[10px] text-gray-500">AI Engine Active • ML Model Ready</p>
                </div>
            </div>
        </aside>
    )
}
