import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchInverters } from '../services/api'
import RiskBadge from '../components/RiskBadge'

const STATUS_ICONS = {
    active: '🟢',
    warning: '🟡',
    critical: '🔴',
    offline: '⚫',
}

export default function Monitoring() {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [filters, setFilters] = useState({ block: '', status: '', risk_category: '' })
    const navigate = useNavigate()

    useEffect(() => {
        const params = {}
        if (filters.block) params.block = filters.block
        if (filters.status) params.status = filters.status
        if (filters.risk_category) params.risk_category = filters.risk_category

        setLoading(true)
        fetchInverters(params)
            .then(setData)
            .catch(console.error)
            .finally(() => setLoading(false))
    }, [filters])

    const updateFilter = (key, value) => {
        setFilters(prev => ({ ...prev, [key]: value }))
    }

    return (
        <div className="space-y-6 max-w-7xl">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">
                    <span className="text-gradient">Inverter</span> Monitoring
                </h1>
                <p className="text-gray-500 mt-1">Monitor all inverters across the solar plant</p>
            </div>

            {/* Filters */}
            <div className="flex flex-wrap gap-3">
                <select
                    className="input-field w-auto min-w-[140px]"
                    value={filters.block}
                    onChange={e => updateFilter('block', e.target.value)}
                >
                    <option value="">All Blocks</option>
                    <option value="A">Block A</option>
                    <option value="B">Block B</option>
                    <option value="C">Block C</option>
                    <option value="D">Block D</option>
                </select>

                <select
                    className="input-field w-auto min-w-[140px]"
                    value={filters.risk_category}
                    onChange={e => updateFilter('risk_category', e.target.value)}
                >
                    <option value="">All Risk Levels</option>
                    <option value="no_risk">No Risk</option>
                    <option value="degradation_risk">Degradation Risk</option>
                    <option value="shutdown_risk">Shutdown Risk</option>
                </select>

                <select
                    className="input-field w-auto min-w-[140px]"
                    value={filters.status}
                    onChange={e => updateFilter('status', e.target.value)}
                >
                    <option value="">All Statuses</option>
                    <option value="active">Active</option>
                    <option value="warning">Warning</option>
                    <option value="critical">Critical</option>
                    <option value="offline">Offline</option>
                </select>

                {(filters.block || filters.status || filters.risk_category) && (
                    <button
                        className="btn-secondary text-sm"
                        onClick={() => setFilters({ block: '', status: '', risk_category: '' })}
                    >
                        ✕ Clear Filters
                    </button>
                )}
            </div>

            {/* Results count */}
            <p className="text-sm text-gray-500">
                Showing {data?.total ?? 0} inverter{data?.total !== 1 ? 's' : ''}
            </p>

            {/* Table */}
            <div className="glass-card overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center p-12">
                        <div className="w-8 h-8 border-2 border-solar-500 border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-white/10">
                                <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Inverter</th>
                                <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Location</th>
                                <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Status</th>
                                <th className="text-left px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Risk</th>
                                <th className="text-right px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Temp</th>
                                <th className="text-right px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Power</th>
                                <th className="text-right px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Efficiency</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data?.inverters?.map(inv => (
                                <tr
                                    key={inv.inverter_id}
                                    className="table-row"
                                    onClick={() => navigate(`/inverter/${inv.inverter_id}`)}
                                >
                                    <td className="px-6 py-4">
                                        <span className="font-semibold text-white">{inv.inverter_id}</span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-400">{inv.location}</td>
                                    <td className="px-6 py-4">
                                        <span className="flex items-center gap-2 text-sm">
                                            {STATUS_ICONS[inv.status]} {inv.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <RiskBadge category={inv.risk_category} score={inv.risk_score} />
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <span className={`text-sm font-mono ${inv.temperature > 60 ? 'text-red-400' : inv.temperature > 50 ? 'text-amber-400' : 'text-gray-300'}`}>
                                            {inv.temperature}°C
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right text-sm font-mono text-gray-300">
                                        {(inv.power_output / 1000).toFixed(1)} kW
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <span className={`text-sm font-mono ${inv.efficiency < 93 ? 'text-red-400' : inv.efficiency < 96 ? 'text-amber-400' : 'text-emerald-400'}`}>
                                            {inv.efficiency}%
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    )
}
