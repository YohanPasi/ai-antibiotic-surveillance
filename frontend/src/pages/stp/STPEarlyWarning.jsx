import React, { useState, useEffect } from 'react';
import { ShieldAlert, AlertTriangle, BellRing, TrendingUp, Info } from 'lucide-react';
import RiskCard from '../../components/stp/RiskCard';
import SHAPSummary from '../../components/stp/SHAPSummary';

const API = 'http://localhost:8000';

const RISK_CONFIG = {
    high: { label: 'High Risk', badge: 'bg-red-100 text-red-700 border-red-200', icon: <ShieldAlert className="w-4 h-4 text-red-500" /> },
    medium: { label: 'Moderate Risk', badge: 'bg-amber-100 text-amber-700 border-amber-200', icon: <AlertTriangle className="w-4 h-4 text-amber-500" /> },
    low: { label: 'Low Risk', badge: 'bg-blue-100 text-blue-700 border-blue-200', icon: <BellRing className="w-4 h-4 text-blue-500" /> },
};

const STPEarlyWarning = () => {
    const [predictions, setPredictions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch(`${API}/api/stp/stage3/early-warning-cards`)
            .then(r => { if (!r.ok) throw new Error(); return r.json(); })
            .then(data => setPredictions(data.data || []))
            .catch(() => setError('Could not load early warnings'))
            .finally(() => setLoading(false));
    }, []);

    const formatDate = (iso) => {
        try { return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }); }
        catch { return iso; }
    };

    if (loading) return (
        <div className="flex items-center justify-center h-64">
            <div className="text-center">
                <div className="w-10 h-10 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <p className="text-slate-500">Loading warning signals…</p>
            </div>
        </div>
    );

    if (error) return (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center text-red-600">{error}</div>
    );

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Early Warning Signals</h1>
                    <p className="text-sm text-slate-500 mt-0.5">Resistance patterns likely to worsen in the next 7 days</p>
                </div>
                <span className="self-start sm:self-auto flex items-center gap-1.5 px-3 py-1.5 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold border border-purple-200">
                    <TrendingUp className="w-3.5 h-3.5" /> Next 7 Days
                </span>
            </div>

            {/* Notice */}
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-3">
                <ShieldAlert className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-amber-800 leading-relaxed">
                    These are <strong>early warning signals</strong> to support infection prevention planning.
                    They are <strong>not</strong> diagnostic results and must not be used for individual patient care decisions.
                </p>
            </div>

            {predictions.length === 0 ? (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 py-16 text-center">
                    <BellRing className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
                    <p className="font-semibold text-slate-600 dark:text-gray-300">No early warnings at this time</p>
                    <p className="text-sm text-slate-400 mt-1">The system is not detecting any significant resistance changes</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                    {predictions.map((pred, idx) => {
                        const riskLevel = pred.prediction?.risk || 'low';
                        const cfg = RISK_CONFIG[riskLevel] || RISK_CONFIG.low;
                        const prob = pred.prediction?.probability ?? 0;

                        return (
                            <div key={idx} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow overflow-hidden">
                                {/* Card Header */}
                                <div className="px-5 pt-5 pb-4 border-b border-gray-50 dark:border-gray-700">
                                    <div className="flex items-start justify-between gap-3">
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                {cfg.icon}
                                                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${cfg.badge}`}>{cfg.label}</span>
                                            </div>
                                            <h3 className="font-bold text-slate-800 dark:text-white">{pred.organism}</h3>
                                            <p className="text-sm text-slate-500 mt-0.5">{pred.ward} · {pred.antibiotic}</p>
                                        </div>
                                        <div className="text-right flex-shrink-0">
                                            <div className={`text-2xl font-black ${prob > 0.7 ? 'text-red-600' : prob > 0.4 ? 'text-amber-600' : 'text-blue-600'}`}>
                                                {(prob * 100).toFixed(0)}%
                                            </div>
                                            <div className="text-xs text-slate-400">likelihood</div>
                                        </div>
                                    </div>
                                    {pred.detected_week && (
                                        <div className="flex gap-4 mt-3 text-xs text-slate-500">
                                            <span>Detected: {formatDate(pred.detected_week)}</span>
                                            {pred.forecast_week && <span>→ Forecast for: {formatDate(pred.forecast_week)}</span>}
                                        </div>
                                    )}
                                </div>

                                {/* Card Body */}
                                <div className="px-5 pt-4 pb-5">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <p className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Risk Level</p>
                                            <RiskCard
                                                ward={pred.ward}
                                                organism={pred.organism}
                                                antibiotic={pred.antibiotic}
                                                probability={prob}
                                                riskLevel={riskLevel}
                                                uncertainty={pred.prediction?.uncertainty}
                                                horizon={pred.prediction?.horizon}
                                                compact
                                            />
                                        </div>
                                        <div>
                                            <p className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">Key Factors</p>
                                            <SHAPSummary features={pred.features} />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Legend */}
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-700 p-4">
                <div className="flex items-start gap-3">
                    <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
                    <div className="text-xs text-slate-500 space-y-1">
                        <p><strong className="text-slate-600">How to read this page:</strong> Each card shows a location and organism where resistance is expected to increase.</p>
                        <p>The <strong>likelihood percentage</strong> reflects how probable the system estimates a resistance increase is in the next 7 days. Higher % = more urgent attention needed.</p>
                        <p><strong>Key Factors</strong> show what patterns are influencing the warning signal.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default STPEarlyWarning;
