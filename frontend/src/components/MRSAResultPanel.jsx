import React, { useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const validateProps = props => {
    if (props.prediction && (props.prediction.forecast || props.prediction.baseline || props.prediction.matrix)) {
        throw new Error('SECURITY: Forecasting data detected in MRSA panel.');
    }
};

const RISK = {
    RED: { label: 'High Risk', color: '#ef4444', bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-300 dark:border-red-600', text: 'text-red-600 dark:text-red-400', barColor: 'bg-red-500' },
    AMBER: { label: 'Intermediate Risk', color: '#f59e0b', bg: 'bg-amber-50 dark:bg-amber-900/20', border: 'border-amber-300 dark:border-amber-500', text: 'text-amber-600 dark:text-amber-400', barColor: 'bg-amber-500' },
    GREEN: { label: 'Low Risk', color: '#22c55e', bg: 'bg-green-50 dark:bg-green-900/20', border: 'border-green-300 dark:border-green-600', text: 'text-green-600 dark:text-green-400', barColor: 'bg-green-500' },
};

const AGREEMENT = {
    HIGH: { label: 'Strong agreement between methods', color: 'text-green-600 dark:text-green-400', dot: 'bg-green-400' },
    MODERATE: { label: 'Partial agreement between methods', color: 'text-amber-600 dark:text-amber-400', dot: 'bg-amber-400' },
    LOW: { label: 'Mixed results — methods disagreed', color: 'text-red-600 dark:text-red-400', dot: 'bg-red-400' },
};

const MODEL_LABELS = {
    rf: { name: 'Analysis A', role: 'Primary' },
    lr: { name: 'Analysis B', role: 'Reference' },
    xgb: { name: 'Analysis C', role: 'Confirmatory' },
};

const MRSAResultPanel = ({ prediction, loading }) => {
    if (prediction) validateProps({ prediction });

    const [explanation, setExplanation] = useState(null);
    const [explaining, setExplaining] = useState(false);
    const [expError, setExpError] = useState(null);
    const [showMethods, setShowMethods] = useState(false);

    useEffect(() => {
        setExplanation(null);
        setExpError(null);
    }, [prediction]);

    // Empty state
    if (!prediction && !loading) return (
        <div className="bg-white dark:bg-slate-800/50 rounded-xl h-full min-h-[500px] flex flex-col items-center justify-center text-center px-8">
            <div className="w-12 h-12 rounded-lg bg-slate-100 dark:bg-slate-700 flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-slate-500 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
            </div>
            <p className="text-slate-800 dark:text-slate-300 font-medium">No result yet</p>
            <p className="text-slate-500 dark:text-slate-500 text-sm mt-1 max-w-xs">
                Fill in the patient details and click <strong className="text-slate-600 dark:text-slate-400">Get Screening Result</strong> to see the MRSA risk assessment.
            </p>
        </div>
    );

    // Loading state
    if (loading) return (
        <div className="bg-white dark:bg-slate-800/50 rounded-xl h-full min-h-[500px] flex flex-col items-center justify-center text-center">
            <svg className="w-8 h-8 text-blue-400 animate-spin mb-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-slate-800 dark:text-slate-300 font-medium">Analysing specimen data...</p>
            <p className="text-slate-500 dark:text-slate-500 text-sm mt-1">Running all screening methods</p>
        </div>
    );

    const { risk_band, mrsa_probability, stewardship_message, assessment_id, consensus_details } = prediction;
    const pct = (mrsa_probability * 100).toFixed(1);
    const risk = RISK[risk_band] || RISK.GREEN;
    const agreement = consensus_details ? (AGREEMENT[consensus_details.confidence_level] || AGREEMENT.LOW) : null;

    const handleExplain = async () => {
        setExplaining(true);
        setExpError(null);
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`http://localhost:8000/api/mrsa/explain/${assessment_id}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            if (!res.ok) throw new Error(`Failed to load risk factors (${res.status})`);
            setExplanation(await res.json());
        } catch (err) {
            setExpError(err.message);
        } finally {
            setExplaining(false);
        }
    };

    return (
        <div className="space-y-4">

            {/* ── Main Result Card ── */}
            <div className={`bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden border-l-4 ${risk.border}`}>
                <div className="p-6">
                    <div className="flex items-start justify-between gap-4 mb-6">
                        <div>
                            <p className="text-xs font-medium text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1">Screening Result</p>
                            <h2 className={`text-2xl font-bold ${risk.text}`}>{risk.label}</h2>
                            {agreement && (
                                <p className={`text-sm mt-1 ${agreement.color}`}>
                                    <span className={`inline-block w-1.5 h-1.5 rounded-full ${agreement.dot} mr-1.5 mb-0.5`} />
                                    {agreement.label}
                                </p>
                            )}
                        </div>
                        <div className="text-right flex-shrink-0">
                            <span className={`text-4xl font-bold ${risk.text}`}>{pct}%</span>
                            <p className="text-xs text-slate-500 dark:text-slate-500 mt-0.5">Probability of MRSA</p>
                        </div>
                    </div>

                    {/* Probability bar */}
                    <div className="mb-2">
                        <div className="flex justify-between text-xs text-slate-500 dark:text-slate-500 mb-1.5">
                            <span>0% — Low risk</span>
                            <span>100% — High risk</span>
                        </div>
                        <div className="h-3 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                            <div
                                className={`h-full rounded-full transition-all duration-700 ${risk.barColor}`}
                                style={{ width: `${pct}%` }}
                            />
                        </div>
                        {/* Threshold markers */}
                        <div className="relative h-4 mt-1">
                            <span className="absolute text-[10px] text-slate-500 dark:text-slate-500" style={{ left: '30%', transform: 'translateX(-50%)' }}>30%</span>
                            <span className="absolute text-[10px] text-slate-500 dark:text-slate-500" style={{ left: '60%', transform: 'translateX(-50%)' }}>60%</span>
                            <div className="absolute h-2 w-px bg-slate-200 dark:bg-slate-600" style={{ left: '30%', top: 0 }} />
                            <div className="absolute h-2 w-px bg-slate-200 dark:bg-slate-600" style={{ left: '60%', top: 0 }} />
                        </div>
                    </div>

                    {/* Record ID */}
                    <p className="text-xs text-slate-500 dark:text-slate-500 mt-3">Record #{assessment_id} · Screening v1.0</p>
                </div>

                {/* Clinical Recommendation */}
                <div className="px-6 pb-6">
                    <div className={`p-4 rounded-lg border ${risk.bg} ${risk.border} border-opacity-40`}>
                        <p className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1.5">Clinical Recommendation</p>
                        <p className="text-sm text-slate-900 dark:text-slate-200 leading-relaxed">{stewardship_message}</p>
                    </div>
                </div>
            </div>

            {/* ── Screening Methods (collapsible) ── */}
            {consensus_details && (
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
                    <button
                        onClick={() => setShowMethods(!showMethods)}
                        className="w-full flex items-center justify-between px-5 py-3.5 text-left hover:bg-slate-100 dark:bg-slate-700/50 transition-colors"
                    >
                        <span className="text-sm font-medium text-slate-800 dark:text-slate-300">View all screening methods</span>
                        <svg className={`w-4 h-4 text-slate-500 dark:text-slate-500 transition-transform ${showMethods ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                    </button>

                    {showMethods && (
                        <div className="border-t border-slate-200 dark:border-slate-700 p-5">
                            {consensus_details.confidence_level !== 'HIGH' && (
                                <div className="mb-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-700 text-amber-300 text-sm">
                                    ⚠ Screening methods gave mixed results. Use the higher risk estimate as a precaution and review clinically.
                                </div>
                            )}
                            <div className="space-y-3">
                                {Object.entries(consensus_details.models).map(([key, model]) => {
                                    const info = MODEL_LABELS[key] || { name: key.toUpperCase(), role: '' };
                                    const r = RISK[model.band] || RISK.GREEN;
                                    const p = (model.prob * 100).toFixed(0);
                                    return (
                                        <div key={key} className="flex items-center gap-4 p-3 bg-slate-100 dark:bg-slate-700/40 rounded-lg">
                                            <div className="min-w-0 flex-1">
                                                <div className="flex items-center gap-2 mb-1.5">
                                                    <span className="text-sm font-medium text-slate-900 dark:text-slate-200">{info.name}</span>
                                                    <span className="text-xs text-slate-500 dark:text-slate-500">{info.role}</span>
                                                </div>
                                                <div className="h-1.5 bg-slate-200 dark:bg-slate-600 rounded-full overflow-hidden">
                                                    <div className={`h-full rounded-full ${r.barColor}`} style={{ width: `${p}%` }} />
                                                </div>
                                            </div>
                                            <div className="text-right flex-shrink-0">
                                                <span className={`text-base font-bold ${r.text}`}>{p}%</span>
                                                <br />
                                                <span className={`text-xs font-medium ${r.text}`}>{model.band}</span>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ── Why this result? ── */}
            <div className="text-center">
                <button
                    onClick={handleExplain}
                    disabled={explaining}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium text-slate-800 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:bg-slate-600 border border-slate-300 dark:border-slate-600 disabled:opacity-50 transition-colors"
                >
                    {explaining ? (
                        <>
                            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            Loading risk factors...
                        </>
                    ) : (
                        <>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Why this result?
                        </>
                    )}
                </button>
                {expError && <p className="text-red-600 dark:text-red-400 text-xs mt-2">{expError}</p>}
            </div>

            {/* ── Risk Factor Explanation ── */}
            {explanation && (
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
                    <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
                        <div>
                            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200">Key Risk Factors</h3>
                            <p className="text-xs text-slate-500 dark:text-slate-500 mt-0.5">Top features influencing this screening result</p>
                        </div>
                        <button onClick={() => setExplanation(null)} className="text-slate-500 dark:text-slate-500 hover:text-slate-800 dark:text-slate-300 transition-colors">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    <div className="p-5 space-y-2 max-h-72 overflow-y-auto">
                        {explanation.explanations.map((item, idx) => {
                            const isRisk = item.impact > 0;
                            const abs = Math.abs(item.impact);
                            const barPct = Math.min(100, (abs / 0.25) * 100);
                            return (
                                <div key={idx} className="flex items-center gap-3 py-2 border-b border-slate-200 dark:border-slate-700 last:border-0">
                                    <span className="w-5 h-5 flex-shrink-0 rounded bg-slate-100 dark:bg-slate-700 text-center text-[10px] font-bold text-slate-600 dark:text-slate-400 leading-5">{idx + 1}</span>
                                    <div className="flex-1 min-w-0">
                                        <span className="block text-sm text-slate-900 dark:text-slate-200 truncate">{item.feature}</span>
                                        {item.value && <span className="text-xs text-slate-500 dark:text-slate-500">Recorded: {item.value}</span>}
                                        <div className="mt-1 h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full rounded-full ${isRisk ? 'bg-red-500' : 'bg-green-500'}`}
                                                style={{ width: `${barPct}%` }}
                                            />
                                        </div>
                                    </div>
                                    <span className={`text-xs font-medium flex-shrink-0 ${isRisk ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
                                        {isRisk ? '▲ Raises suspicion' : '▼ Lowers suspicion'}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MRSAResultPanel;
