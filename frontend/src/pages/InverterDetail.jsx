import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchInverter, fetchInverterMetrics, predictRisk } from '../services/api'
import RiskBadge from '../components/RiskBadge'
import {
    AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid, Cell
} from 'recharts'

const CHART_TOOLTIP_STYLE = {
    contentStyle: { backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '12px' },
    itemStyle: { color: '#fff' },
    labelStyle: { color: '#94a3b8' },
}

export default function InverterDetail() {
    const { id } = useParams()
    const [inverter, setInverter] = useState(null)
    const [metrics, setMetrics] = useState(null)
    const [prediction, setPrediction] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        Promise.all([
            fetchInverter(id),
            fetchInverterMetrics(id),
        ])
            .then(([inv, met]) => {
                setInverter(inv)
                setMetrics(met)
                // Auto-predict using current telemetry
                return predictRisk({ inverter_id: id, telemetry: inv.telemetry })
            })
            .then(setPrediction)
            .catch(console.error)
            .finally(() => setLoading(false))
    }, [id])

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="w-8 h-8 border-2 border-solar-500 border-t-transparent rounded-full animate-spin" />
            </div>
        )
    }

    if (!inverter) {
        return (
            <div className="text-center py-20">
                <p className="text-gray-400">Inverter {id} not found.</p>
                <Link to="/monitoring" className="btn-primary mt-4 inline-block">Back to Monitoring</Link>
            </div>
        )
    }

    const meta = inverter.metadata
    const tel = inverter.telemetry

    // Downsample metrics to every 4h for cleaner charts
    const downsample = (arr) => arr?.filter((_, i) => i % 4 === 0).map(p => ({
        time: new Date(p.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit' }),
        value: p.value
    })) || []

    return (
        <div className="space-y-6 max-w-7xl">
            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-sm text-gray-500">
                <Link to="/monitoring" className="hover:text-solar-400 transition-colors">Monitoring</Link>
                <span>/</span>
                <span className="text-white">{id}</span>
            </div>

            {/* Header */}
            <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-white">{meta.inverter_id}</h1>
                    <p className="text-gray-500 mt-1">{meta.location} • {meta.manufacturer} {meta.model}</p>
                </div>
                <RiskBadge category={inverter.risk_category} score={inverter.risk_score} />
            </div>

            {/* Metadata + Telemetry Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Metadata */}
                <div className="glass-card p-6">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Inverter Details</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        {[
                            ['Capacity', `${meta.capacity_kw} kW`],
                            ['Block', meta.block],
                            ['Installed', meta.installation_date],
                            ['Status', inverter.status],
                            ['Runtime', `${(tel.inverter_runtime / 1000).toFixed(1)}k hours`],
                            ['Last Update', new Date(inverter.last_update).toLocaleString()],
                        ].map(([label, value]) => (
                            <div key={label}>
                                <span className="text-gray-500 block text-xs">{label}</span>
                                <span className="text-white font-medium capitalize">{value}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Live Telemetry */}
                <div className="glass-card p-6">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Current Telemetry</h3>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                        {[
                            ['DC Voltage', `${tel.dc_voltage} V`, tel.dc_voltage < 500 && tel.dc_voltage > 0 ? 'text-red-400' : 'text-white'],
                            ['AC Voltage', `${tel.ac_voltage} V`, ''],
                            ['Current', `${tel.current} A`, ''],
                            ['Power', `${(tel.power_output / 1000).toFixed(1)} kW`, ''],
                            ['Temperature', `${tel.temperature}°C`, tel.temperature > 60 ? 'text-red-400' : tel.temperature > 50 ? 'text-amber-400' : ''],
                            ['Efficiency', `${tel.efficiency}%`, tel.efficiency < 93 ? 'text-red-400' : tel.efficiency < 96 ? 'text-amber-400' : 'text-emerald-400'],
                            ['Daily Gen', `${tel.daily_generation} kWh`, ''],
                            ['Alarms (24h)', tel.alarm_frequency, tel.alarm_frequency > 5 ? 'text-red-400' : ''],
                        ].map(([label, value, cls]) => (
                            <div key={label}>
                                <span className="text-gray-500 block text-xs">{label}</span>
                                <span className={`font-mono font-medium ${cls || 'text-white'}`}>{value}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* GenAI Summary */}
            {prediction && (
                <div className="glass-card p-6 border-l-4 border-solar-500">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                        🤖 AI Risk Assessment
                    </h3>
                    <div className="flex items-center gap-4 mb-3">
                        <RiskBadge category={prediction.risk_category} score={prediction.risk_score} />
                    </div>
                    <div className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
                        {prediction.genai_summary}
                    </div>
                </div>
            )}

            {/* SHAP Feature Importance */}
            {prediction?.top_feature_contributions && (
                <div className="glass-card p-6">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
                        Feature Importance (SHAP)
                    </h3>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart
                            data={prediction.top_feature_contributions.map(f => ({
                                feature: f.feature.replace(/_/g, ' '),
                                importance: f.importance,
                                fill: f.direction === 'increasing_risk' ? '#ef4444' : '#10b981'
                            }))}
                            layout="vertical"
                            margin={{ left: 120 }}
                        >
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                            <YAxis type="category" dataKey="feature" tick={{ fill: '#94a3b8', fontSize: 11 }} width={110} />
                            <Tooltip {...CHART_TOOLTIP_STYLE} />
                            <Bar dataKey="importance" radius={[0, 6, 6, 0]}>
                                {prediction.top_feature_contributions.map((f, i) => (
                                    <Cell key={i} fill={f.direction === 'increasing_risk' ? '#ef4444' : '#10b981'} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                    <div className="flex gap-6 mt-2 justify-center">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-500" />
                            <span className="text-xs text-gray-400">Increasing Risk</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-emerald-500" />
                            <span className="text-xs text-gray-400">Decreasing Risk</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Time-Series Charts */}
            {metrics && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {[
                        { key: 'power_output', label: 'Power Output (W)', color: '#fbbf24' },
                        { key: 'temperature', label: 'Temperature (°C)', color: '#ef4444' },
                        { key: 'dc_voltage', label: 'DC Voltage (V)', color: '#4263eb' },
                        { key: 'efficiency', label: 'Efficiency (%)', color: '#10b981' },
                    ].map(chart => (
                        <div key={chart.key} className="glass-card p-6">
                            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">{chart.label}</h3>
                            <ResponsiveContainer width="100%" height={200}>
                                <AreaChart data={downsample(metrics[chart.key])}>
                                    <defs>
                                        <linearGradient id={`grad-${chart.key}`} x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor={chart.color} stopOpacity={0.3} />
                                            <stop offset="100%" stopColor={chart.color} stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                    <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 10 }} interval="preserveEnd" />
                                    <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
                                    <Tooltip {...CHART_TOOLTIP_STYLE} />
                                    <Area
                                        type="monotone"
                                        dataKey="value"
                                        stroke={chart.color}
                                        strokeWidth={2}
                                        fill={`url(#grad-${chart.key})`}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

