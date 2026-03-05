export default function RiskBadge({ category, score }) {
    const config = {
        no_risk: { label: 'No Risk', className: 'badge-success' },
        degradation_risk: { label: 'Degradation', className: 'badge-warning' },
        shutdown_risk: { label: 'Shutdown Risk', className: 'badge-danger' },
    }

    const { label, className } = config[category] || config.no_risk

    return (
        <div className="flex items-center gap-2">
            <span className={className}>{label}</span>
            {score !== undefined && (
                <span className="text-xs text-gray-500">{(score * 100).toFixed(0)}%</span>
            )}
        </div>
    )
}
