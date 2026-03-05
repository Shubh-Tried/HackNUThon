import { useState, useEffect } from 'react'
import { fetchDashboardSummary, fetchPlantMetrics, askQuestion } from '../services/api'
import StatCard from '../components/StatCard'
import {
    PieChart, Pie, Cell, AreaChart, Area, BarChart, Bar,
    XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts'

const RISK_COLORS = { no_risk: '#10b981', degradation_risk: '#f59e0b', shutdown_risk: '#ef4444' }

const CHART_TOOLTIP = {
    contentStyle: { backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '12px' },
    itemStyle: { color: '#fff' },
    labelStyle: { color: '#94a3b8' },
}

export default function Dashboard() {
    const [data, setData] = useState(null)
    const [metrics, setMetrics] = useState(null)
    const [question, setQuestion] = useState('')
    const [answer, setAnswer] = useState(null)
    const [asking, setAsking] = useState(false)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        Promise.all([
            fetchDashboardSummary(),
            fetchPlantMetrics(),
        ])
            .then(([summaryData, plantMetrics]) => {
                setData(summaryData)
                setMetrics(plantMetrics)
            })
            .catch(console.error)
            .finally(() => setLoading(false))
    }, [])

    const handleAsk = async (e) => {
        e.preventDefault()
        if (!question.trim()) return
        setAsking(true)
        try {
            const result = await askQuestion(question)
            setAnswer(result)
        } catch (err) {
            setAnswer({ answer: 'Failed to get a response. Please check if the backend is running.', confidence: 0 })
        }
        setAsking(false)
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="w-8 h-8 border-2 border-solar-500 border-t-transparent rounded-full animate-spin" />
            </div>
        )
    }

    const summary = data?.summary
    const riskData = summary ? Object.entries(summary.risk_distribution).map(([key, val]) => ({
        name: key.replace('_', ' ').replace('risk', '').trim() || 'no risk',
        value: val,
        color: RISK_COLORS[key]
    })) : []

    // Downsample metrics to every 6h for cleaner charts
    const downsample = (arr) => arr?.filter((_, i) => i % 6 === 0).map(p => ({
        time: new Date(p.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit' }),
        value: p.value
    })) || []

    return (
        <div className="space-y-8 max-w-7xl">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold">
                    <span className="text-gradient">Solar Plant</span> Dashboard
                </h1>
                <p className="text-gray-500 mt-1">Real-time inverter monitoring and AI-driven failure prediction</p>
            </div>

            {/* Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <StatCard title="Total Inverters" value={summary?.total_inverters} icon="⚡" color="blue"
                    subtitle={`${summary?.active_inverters} active, ${summary?.total_inverters - summary?.active_inverters} inactive`} />
                <StatCard title="Active" value={summary?.active_inverters} icon="✅" color="emerald"
                    subtitle={`${((summary?.active_inverters / summary?.total_inverters) * 100).toFixed(0)}% of fleet`} />
                <StatCard title="At Risk" value={summary?.inverters_at_risk} icon="⚠️" color="red"
                    subtitle={`${summary?.risk_distribution?.shutdown_risk || 0} shutdown, ${summary?.risk_distribution?.degradation_risk || 0} degrading`} />
                <StatCard
                    title="Avg Efficiency"
                    value={`${summary?.average_efficiency}%`}
                    icon="📈"
                    color="solar"
                    subtitle="Computed from active inverters"
                />
                <StatCard
                    title="Total Power"
                    value={`${(summary?.total_power_output / 1000).toFixed(1)} kW`}
                    icon="🔋"
                    color="blue"
                    subtitle={`${summary?.total_daily_generation?.toFixed(0)} kWh generated today`}
                />
            </div>

            {/* Row 1: Risk Distribution + Inverters Requiring Attention */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Risk Distribution */}
                <div className="glass-card p-6">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Risk Distribution</h3>
                    <div className="flex items-center justify-center">
                        <ResponsiveContainer width="100%" height={220}>
                            <PieChart>
                                <Pie
                                    data={riskData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={90}
                                    paddingAngle={4}
                                    dataKey="value"
                                    stroke="none"
                                >
                                    {riskData.map((entry, i) => (
                                        <Cell key={i} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip {...CHART_TOOLTIP} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="flex justify-center gap-6 mt-2">
                        {riskData.map(d => (
                            <div key={d.name} className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: d.color }} />
                                <span className="text-xs text-gray-400 capitalize">{d.name} ({d.value})</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* At-Risk Inverters */}
                <div className="glass-card p-6">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Inverters Requiring Attention</h3>
                    <div className="space-y-3">
                        {data?.risk_inverters?.map(inv => (
                            <div key={inv.inverter_id} className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                                <div>
                                    <span className="font-semibold text-white">{inv.inverter_id}</span>
                                    <span className="text-xs text-gray-500 ml-2">{inv.location}</span>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className={`badge ${inv.risk_category === 'shutdown_risk' ? 'badge-danger' : 'badge-warning'}`}>
                                        {inv.risk_category.replace('_', ' ')}
                                    </span>
                                    <span className="text-xs font-mono text-gray-400">{(inv.risk_score * 100).toFixed(0)}%</span>
                                </div>
                            </div>
                        ))}
                        {(!data?.risk_inverters || data.risk_inverters.length === 0) && (
                            <p className="text-gray-500 text-sm">All inverters are operating normally.</p>
                        )}
                    </div>
                </div>
            </div>

            {/* Row 2: Plant-Wide Trend Charts */}
            {metrics && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Plant Efficiency Trend */}
                    <div className="glass-card p-6">
                        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-1">Plant Efficiency (7-Day)</h3>
                        <p className="text-[10px] text-gray-600 mb-4">Weighted average across all producing inverters</p>
                        <ResponsiveContainer width="100%" height={200}>
                            <AreaChart data={downsample(metrics.efficiency)}>
                                <defs>
                                    <linearGradient id="grad-eff" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                                        <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 9 }} interval="preserveEnd" />
                                <YAxis domain={['dataMin - 2', 'dataMax + 2']} tick={{ fill: '#64748b', fontSize: 10 }} />
                                <Tooltip {...CHART_TOOLTIP} />
                                <Area type="monotone" dataKey="value" stroke="#10b981" strokeWidth={2} fill="url(#grad-eff)" name="Efficiency %" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Total Power Output Trend */}
                    <div className="glass-card p-6">
                        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-1">Total Power Output (7-Day)</h3>
                        <p className="text-[10px] text-gray-600 mb-4">Sum of all inverter outputs (kW)</p>
                        <ResponsiveContainer width="100%" height={200}>
                            <AreaChart data={downsample(metrics.power_kw)}>
                                <defs>
                                    <linearGradient id="grad-pwr" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#fbbf24" stopOpacity={0.3} />
                                        <stop offset="100%" stopColor="#fbbf24" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 9 }} interval="preserveEnd" />
                                <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
                                <Tooltip {...CHART_TOOLTIP} />
                                <Area type="monotone" dataKey="value" stroke="#fbbf24" strokeWidth={2} fill="url(#grad-pwr)" name="Power (kW)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Average Temperature Trend */}
                    <div className="glass-card p-6">
                        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-1">Avg Temperature (7-Day)</h3>
                        <p className="text-[10px] text-gray-600 mb-4">Mean across all inverter sensors</p>
                        <ResponsiveContainer width="100%" height={200}>
                            <AreaChart data={downsample(metrics.temperature)}>
                                <defs>
                                    <linearGradient id="grad-tmp" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} />
                                        <stop offset="100%" stopColor="#ef4444" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                <XAxis dataKey="time" tick={{ fill: '#64748b', fontSize: 9 }} interval="preserveEnd" />
                                <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
                                <Tooltip {...CHART_TOOLTIP} />
                                <Area type="monotone" dataKey="value" stroke="#ef4444" strokeWidth={2} fill="url(#grad-tmp)" name="Temp (°C)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            {/* Row 3: Block Comparison */}
            {data?.block_comparison && (
                <div className="glass-card p-6">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-1">Block Performance Comparison</h3>
                    <p className="text-[10px] text-gray-600 mb-4">Average efficiency and total power per block — computed from actual inverter telemetry</p>
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={data.block_comparison} margin={{ left: 10 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="block" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                            <YAxis yAxisId="left" tick={{ fill: '#10b981', fontSize: 10 }} label={{ value: 'Efficiency %', angle: -90, position: 'insideLeft', fill: '#10b981', fontSize: 10 }} />
                            <YAxis yAxisId="right" orientation="right" tick={{ fill: '#fbbf24', fontSize: 10 }} label={{ value: 'Power (kW)', angle: 90, position: 'insideRight', fill: '#fbbf24', fontSize: 10 }} />
                            <Tooltip {...CHART_TOOLTIP} />
                            <Bar yAxisId="left" dataKey="efficiency" fill="#10b981" radius={[6, 6, 0, 0]} name="Avg Efficiency %" barSize={40} />
                            <Bar yAxisId="right" dataKey="power_kw" fill="#fbbf24" radius={[6, 6, 0, 0]} name="Total Power (kW)" barSize={40} />
                        </BarChart>
                    </ResponsiveContainer>
                    <div className="flex justify-center gap-8 mt-2">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded bg-emerald-500" />
                            <span className="text-xs text-gray-400">Avg Efficiency (%)</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded bg-solar-400" />
                            <span className="text-xs text-gray-400">Total Power (kW)</span>
                        </div>
                    </div>
                </div>
            )}

            {/* AI Q&A Section */}
            <div className="glass-card p-6">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
                    🤖 AI Assistant — Ask About Your Plant
                </h3>
                <form onSubmit={handleAsk} className="flex gap-3">
                    <input
                        type="text"
                        className="input-field flex-1"
                        placeholder='Try: "Which inverters have elevated risk?" or "Why is INV-203 at risk?"'
                        value={question}
                        onChange={e => setQuestion(e.target.value)}
                    />
                    <button type="submit" className="btn-primary whitespace-nowrap" disabled={asking}>
                        {asking ? 'Analyzing...' : 'Ask AI'}
                    </button>
                </form>
                {answer && (
                    <div className="mt-4 p-4 rounded-xl bg-white/5 border border-white/5">
                        <div className="flex items-center gap-2 mb-2">
                            <span className="text-xs text-gray-500">Confidence: {(answer.confidence * 100).toFixed(0)}%</span>
                            {answer.referenced_inverters?.length > 0 && (
                                <span className="text-xs text-gray-500">
                                    • Referenced: {answer.referenced_inverters.join(', ')}
                                </span>
                            )}
                        </div>
                        <div className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">{answer.answer}</div>
                    </div>
                )}
            </div>
        </div>
    )
}
