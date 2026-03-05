export default function StatCard({ title, value, subtitle, icon, trend, color = 'solar' }) {
    const colorMap = {
        solar: 'from-solar-500/20 to-solar-600/10 border-solar-500/20',
        emerald: 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/20',
        red: 'from-red-500/20 to-red-600/10 border-red-500/20',
        blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/20',
    }

    const textColorMap = {
        solar: 'text-solar-400',
        emerald: 'text-emerald-400',
        red: 'text-red-400',
        blue: 'text-blue-400',
    }

    return (
        <div className={`stat-card bg-gradient-to-br ${colorMap[color]} border`}>
            <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">{title}</span>
                <span className="text-2xl">{icon}</span>
            </div>
            <div className="flex items-end gap-2">
                <span className={`text-3xl font-bold ${textColorMap[color]}`}>{value}</span>
                {trend && (
                    <span className={`text-xs font-medium mb-1 ${trend > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
                    </span>
                )}
            </div>
            {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
        </div>
    )
}
