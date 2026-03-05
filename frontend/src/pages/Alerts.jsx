import { useState, useEffect } from 'react'
import { fetchAlerts } from '../services/api'

const SEVERITY_CONFIG = {
    critical: { badge: 'badge-danger', icon: '🔴', bg: 'border-l-red-500' },
    high: { badge: 'badge-danger', icon: '🟠', bg: 'border-l-orange-500' },
    medium: { badge: 'badge-warning', icon: '🟡', bg: 'border-l-amber-500' },
    low: { badge: 'badge-info', icon: '🔵', bg: 'border-l-blue-500' },
}

export default function Alerts() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState('')

    useEffect(() => {
        const params = filter ? { severity: filter } : {}
        setLoading(true)
        fetchAlerts(params)
            .then(setData)
            .catch(console.error)
            .finally(() => setLoading(false))
    }, [filter])

    return (
        <div className="space-y-6 max-w-5xl">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">
                    <span className="text-gradient">Active</span> Alerts
                </h1>
                <p className="text-gray-500 mt-1">Real-time warnings and critical notifications</p>
            </div>

            {/* Severity Filter */}
            <div className="flex gap-2">
                {['', 'critical', 'high', 'medium', 'low'].map(sev => (
                    <button
                        key={sev}
                        className={`px-4 py-2 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all duration-200 ${filter === sev
                                ? 'bg-solar-500/20 text-solar-400 border border-solar-500/30'
                                : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                            }`}
                        onClick={() => setFilter(sev)}
                    >
                        {sev || 'All'} {sev && data ? `(${data.alerts.filter(a => a.severity === sev).length})` : ''}
                    </button>
                ))}
            </div>

            {/* Total */}
            <p className="text-sm text-gray-500">
                {data?.total ?? 0} alert{data?.total !== 1 ? 's' : ''}
            </p>

            {/* Alert Cards */}
            {loading ? (
                <div className="flex items-center justify-center p-12">
                    <div className="w-8 h-8 border-2 border-solar-500 border-t-transparent rounded-full animate-spin" />
                </div>
            ) : (
                <div className="space-y-3">
                    {data?.alerts?.map(alert => {
                        const config = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.low
                        return (
                            <div
                                key={alert.alert_id}
                                className={`glass-card p-5 border-l-4 ${config.bg} transition-all duration-200 hover:bg-white/[0.07]`}
                            >
                                <div className="flex flex-wrap items-start justify-between gap-3">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-3 mb-2">
                                            <span className="text-lg">{config.icon}</span>
                                            <span className="font-bold text-white">{alert.inverter_id}</span>
                                            <span className={config.badge}>{alert.severity}</span>
                                            <span className="badge badge-neutral">{alert.alert_type.replace(/_/g, ' ')}</span>
                                        </div>
                                        <p className="text-sm text-gray-300 leading-relaxed">{alert.message}</p>
                                    </div>
                                    <div className="text-right shrink-0">
                                        <span className="text-xs text-gray-500 font-mono">
                                            {new Date(alert.timestamp).toLocaleString()}
                                        </span>
                                        <div className="text-[10px] text-gray-600 mt-1">{alert.alert_id}</div>
                                    </div>
                                </div>
                            </div>
                        )
                    })}
                    {(!data?.alerts || data.alerts.length === 0) && (
                        <div className="text-center py-12">
                            <p className="text-gray-500">No alerts matching the current filter.</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
