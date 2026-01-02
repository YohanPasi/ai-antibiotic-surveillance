import React from 'react';

export default function PredictionPanel({ prediction, loading, organism, antibiotic }) {
    // 1. Hooks MUST be at the top level
    const [explanation, setExplanation] = React.useState(null);
    const [loadingExplain, setLoadingExplain] = React.useState(false);
    const [showExplainModal, setShowExplainModal] = React.useState(false);

    // Reset explanation when prediction changes
    React.useEffect(() => {
        setExplanation(null);
        setShowExplainModal(false);
    }, [prediction]);

    const handleExplain = async () => {
        if (!prediction?.assessment_id) {
            alert("No assessment ID found. Save the prediction first.");
            return;
        }

        setLoadingExplain(true);
        setShowExplainModal(true);
        try {
            const token = localStorage.getItem("token");
            const res = await fetch(`/api/mrsa/explain/${prediction.assessment_id}`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            const data = await res.json();
            if (res.ok) {
                setExplanation(data.explanations);
            } else {
                console.error("Explain error:", data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoadingExplain(false);
        }
    };

    const getAlertColor = (level) => {
        switch (level) {
            case 'green': return 'bg-accent-green/20 border-accent-green text-accent-green'
            case 'amber': return 'bg-accent-amber/20 border-accent-amber text-accent-amber'
            case 'red': return 'bg-accent-red/20 border-accent-red text-accent-red'
            default: return 'bg-dark-border border-dark-border text-gray-400'
        }
    }

    const getAlertIcon = (level) => {
        switch (level) {
            case 'green': return '🟢'
            case 'amber': return '🟡'
            case 'red': return '🔴'
            default: return '⚪'
        }
    }

    const getAlertText = (level) => {
        switch (level) {
            case 'green': return 'Good Susceptibility'
            case 'amber': return 'Moderate Concern'
            case 'red': return 'High Resistance Risk'
            default: return 'Unknown'
        }
    }

    // 2. Conditional Rendering (AFTER hooks)
    if (loading) {
        return (
            <div className="card">
                <div className="skeleton h-64"></div>
            </div>
        )
    }

    if (!prediction) {
        return (
            <div className="card">
                <div className="text-center text-gray-400 py-12">
                    <div className="text-5xl mb-4">🔮</div>
                    <p>Select parameters to generate prediction</p>
                </div>
            </div>
        )
    }

    // 3. Main Render
    return (
        <div className="space-y-6">
            {/* Main Prediction Card */}
            <div className="card relative">
                <h2 className="text-2xl font-semibold text-primary-400 mb-6">
                    🔮 Next Week Prediction
                </h2>

                {/* Prediction Value */}
                <div className="text-center mb-6">
                    <div className="text-6xl font-bold gradient-text mb-2">
                        {prediction.prediction.toFixed(1)}%
                    </div>
                    <div className="text-gray-400">Predicted Susceptibility</div>
                </div>

                {/* Confidence Interval */}
                {prediction.lower_bound && prediction.upper_bound && (
                    <div className="bg-dark-bg rounded-lg p-4 mb-6">
                        <div className="text-xs text-gray-500 mb-2">95% Confidence Interval</div>
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-400">{prediction.lower_bound.toFixed(1)}%</span>
                            <div className="flex-1 mx-4 h-2 bg-dark-border rounded-full relative">
                                <div
                                    className="absolute h-full bg-gradient-to-r from-primary-600 to-primary-400 rounded-full"
                                    style={{
                                        left: `${prediction.lower_bound}%`,
                                        width: `${prediction.upper_bound - prediction.lower_bound}%`
                                    }}
                                ></div>
                            </div>
                            <span className="text-gray-400">{prediction.upper_bound.toFixed(1)}%</span>
                        </div>
                    </div>
                )}

                {/* Alert Level + Explain Button */}
                <div className={`${getAlertColor(prediction.alert_level)} rounded-lg p-4 border-2 flex flex-col gap-3`}>
                    <div className="flex items-center gap-3">
                        <div className="text-3xl">{getAlertIcon(prediction.alert_level)}</div>
                        <div className="flex-1">
                            <div className="font-semibold text-lg">{getAlertText(prediction.alert_level)}</div>
                            <div className="text-sm opacity-80">Alert Status</div>
                        </div>
                    </div>

                    {/* Explain Button */}
                    <button
                        onClick={handleExplain}
                        className="w-full py-2 bg-dark-bg/30 hover:bg-dark-bg/50 rounded border border-current opacity-80 hover:opacity-100 transition-all text-sm font-medium flex items-center justify-center gap-2"
                    >
                        <span>❓</span> Why this risk?
                    </button>
                </div>

                {/* Explanation Modal (Inline Overlay) */}
                {showExplainModal && (
                    <div className="absolute inset-0 bg-dark-card/95 backdrop-blur-sm z-10 rounded-xl p-6 flex flex-col animate-in fade-in zoom-in-95 duration-200">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-white">🧪 Clinical Logic</h3>
                            <button onClick={() => setShowExplainModal(false)} className="text-gray-400 hover:text-white">✕</button>
                        </div>

                        {loadingExplain ? (
                            <div className="flex-1 flex items-center justify-center">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
                            </div>
                        ) : explanation ? (
                            <div className="space-y-3 overflow-y-auto flex-1 custom-scrollbar">
                                {explanation.map((item, idx) => (
                                    <div key={idx} className="flex justify-between items-center p-2 bg-dark-bg rounded border border-dark-border">
                                        <span className="text-sm font-medium text-gray-200">{item.feature}</span>
                                        <div className="flex items-center gap-2">
                                            <div className="h-1.5 w-16 bg-dark-border rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full ${item.direction === 'increase' ? 'bg-accent-red' : 'bg-accent-green'}`}
                                                    style={{ width: `${Math.min(item.impact_score * 100 * 5, 100)}%` }}
                                                ></div>
                                            </div>
                                            <span className={`text-xs font-bold ${item.direction === 'increase' ? 'text-accent-red' : 'text-accent-green'}`}>
                                                {item.direction === 'increase' ? 'RISK ▲' : 'PROTECT ▼'}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                                <p className="text-xs text-gray-500 mt-2 text-center">Top factors driving this prediction (SHAP)</p>
                            </div>
                        ) : (
                            <div className="text-center text-red-400">Failed to load explanation.</div>
                        )}
                    </div>
                )}
            </div>

            {/* Model Info Card */}
            <div className="card bg-dark-bg/50">
                <h3 className="text-lg font-semibold text-primary-400 mb-4">
                    🤖 Model Info
                </h3>

                <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                        <span className="text-gray-400">Model Used:</span>
                        <span className="text-gray-200 font-medium">{prediction.model_used || "Random Forest (Champion)"}</span>
                    </div>

                    {prediction.mae_score && (
                        <div className="flex justify-between">
                            <span className="text-gray-400">MAE Score:</span>
                            <span className="text-gray-200 font-medium">{prediction.mae_score.toFixed(2)}%</span>
                        </div>
                    )}

                    <div className="flex justify-between">
                        <span className="text-gray-400">Confidence:</span>
                        <span className={`font-medium ${prediction.confidence === 'High' ? 'text-accent-green' :
                            prediction.confidence === 'Medium' ? 'text-accent-amber' :
                                'text-accent-red'
                            }`}>
                            {prediction.confidence || "High"}
                        </span>
                    </div>

                    <div className="flex justify-between">
                        <span className="text-gray-400">Ref ID:</span>
                        <span className="text-gray-500 mono text-xs">#{prediction.assessment_id || "N/A"}</span>
                    </div>
                </div>
            </div>

            {/* Recommendation Card */}
            <div className="card bg-dark-bg/50">
                <h3 className="text-lg font-semibold text-primary-400 mb-4">
                    💡 Recommendation
                </h3>

                <p className="text-sm text-gray-300 leading-relaxed">
                    {prediction.alert_level === 'green' &&
                        `Continue current antimicrobial protocols. ${antibiotic} remains effective against ${organism}.`
                    }
                    {prediction.alert_level === 'amber' &&
                        `Monitor closely. Consider alternative antibiotics if clinical response is poor. Review antimicrobial stewardship guidelines.`
                    }
                    {prediction.alert_level === 'red' &&
                        `⚠️ High resistance predicted. Strongly consider alternative antibiotics. Consult infectious disease specialist and review local antibiograms.`
                    }
                </p>
            </div>
        </div>
    )
}
