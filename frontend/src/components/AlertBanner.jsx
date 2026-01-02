export default function AlertBanner({ alertLevel, prediction, organism, antibiotic }) {
    const getBannerClass = (level) => {
        switch (level) {
            case 'green': return 'bg-accent-green/20 border-accent-green text-accent-green'
            case 'amber': return 'bg-accent-amber/20 border-accent-amber text-accent-amber'
            case 'red': return 'bg-accent-red/20 border-accent-red text-accent-red'
            default: return 'bg-dark-border border-dark-border text-gray-400'
        }
    }

    const getIcon = (level) => {
        switch (level) {
            case 'green': return '✅'
            case 'amber': return '⚠️'
            case 'red': return '🚨'
            default: return 'ℹ️'
        }
    }

    const getMessage = (level) => {
        switch (level) {
            case 'green':
                return `Good susceptibility predicted (${prediction}%). Continue current protocols.`
            case 'amber':
                return `Moderate resistance trend (${prediction}%). Monitor closely and consider alternatives.`
            case 'red':
                return `High resistance risk (${prediction}%). Immediate review required - consult ID specialist.`
            default:
                return 'Analysis complete'
        }
    }

    return (
        <div className={`${getBannerClass(alertLevel)} border-l-4 px-6 py-4 animate-slide-up`}>
            <div className="container mx-auto flex items-center gap-4">
                <div className="text-3xl">{getIcon(alertLevel)}</div>
                <div className="flex-1">
                    <div className="font-semibold text-lg">
                        {getMessage(alertLevel)}
                    </div>
                    <div className="text-sm opacity-90 mt-1">
                        {organism} + {antibiotic} | Next week forecast
                    </div>
                </div>
            </div>
        </div>
    )
}
