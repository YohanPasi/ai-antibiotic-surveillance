import React, { useState } from 'react';

// Safety Guard: Validates that props do not contain forecasting data
const validateProps = (props) => {
    if (props.prediction && (props.prediction.forecast || props.prediction.baseline || props.prediction.matrix)) {
        throw new Error("SECURITY ALERT: Forecasting data detected in MRSA Panel. Isolation breach.");
    }
};

const MRSAResultPanel = ({ prediction, loading }) => {
    // Run safety check immediately
    if (prediction) validateProps({ prediction });

    const [explanation, setExplanation] = useState(null);
    const [explaining, setExplaining] = useState(false);
    const [error, setError] = useState(null);
    const [showConsensus, setShowConsensus] = useState(false);

    // Placeholder content when no prediction
    if (!prediction && !loading) return (
        <div className="h-full flex flex-col justify-center items-center bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-10 text-center opacity-60">
            <div className="w-24 h-24 bg-slate-800 rounded-full flex items-center justify-center mb-6">
                <svg className="w-10 h-10 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
            </div>
            <h3 className="text-xl font-medium text-slate-300">Ready to Analyze</h3>
            <p className="text-slate-500 mt-2 max-w-sm">
                Enter clinical parameters on the left to generate an AI risk assessment.
            </p>
        </div>
    );

    // Loading State handled in parent or here purely for transitions
    if (loading) return (
        <div className="h-full flex justify-center items-center bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl">
            {/* Skeleton or simple spinner is already in button, but this keeps the panel clean */}
        </div>
    );

    const { risk_band, mrsa_probability, stewardship_message, assessment_id, model_version, consensus_details } = prediction;
    const probabilityPercent = (mrsa_probability * 100).toFixed(1);

    // Dynamic Styling based on Risk
    const getRiskStyles = (band) => {
        switch (band) {
            case 'RED': return {
                bg: 'bg-gradient-to-br from-red-500/20 to-red-900/40',
                border: 'border-red-500/50',
                text: 'text-red-400',
                indicator: 'bg-red-500',
                glow: 'shadow-red-900/50'
            };
            case 'AMBER': return {
                bg: 'bg-gradient-to-br from-amber-500/20 to-amber-900/40',
                border: 'border-amber-500/50',
                text: 'text-amber-400',
                indicator: 'bg-amber-500',
                glow: 'shadow-amber-900/50'
            };
            case 'GREEN': return {
                bg: 'bg-gradient-to-br from-emerald-500/20 to-emerald-900/40',
                border: 'border-emerald-500/50',
                text: 'text-emerald-400',
                indicator: 'bg-emerald-500',
                glow: 'shadow-emerald-900/50'
            };
            default: return {
                bg: 'bg-gray-800',
                border: 'border-gray-700',
                text: 'text-gray-400',
                indicator: 'bg-gray-500',
                glow: 'shadow-gray-900/50'
            };
        }
    };

    const styles = getRiskStyles(risk_band);

    // Confidence Styling
    const getConfidenceBadge = (level) => {
        switch (level) {
            case 'HIGH': return <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-bold border border-emerald-500/30">HIGH CONFIDENCE</span>;
            case 'MODERATE': return <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 text-[10px] font-bold border border-amber-500/30">MODERATE CONFIDENCE</span>;
            default: return <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-400 text-[10px] font-bold border border-red-500/30">LOW CONFIDENCE</span>;
        }
    };

    const handleExplain = async () => {
        setExplaining(true);
        setError(null);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`http://localhost:8000/api/mrsa/explain/${assessment_id}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!response.ok) throw new Error(`Explanation fetch failed: ${response.status}`);

            const data = await response.json();
            setExplanation(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setExplaining(false);
        }
    };

    return (
        <div className={`h-full animate-fade-in space-y-6`}>
            {/* Main Result Card */}
            <div className={`relative overflow-hidden rounded-3xl border ${styles.border} ${styles.bg} shadow-2xl ${styles.glow} p-8`}>
                <div className="absolute top-0 right-0 p-6 opacity-30">
                    <div className={`text-9xl font-black ${styles.text} opacity-10 select-none`}>{risk_band[0]}</div>
                </div>

                <div className="relative z-10 flex flex-col h-full justify-between">
                    <div>
                        <div className="flex items-center space-x-3 mb-2">
                            <span className={`px-3 py-1 rounded-full text-xs font-bold tracking-widest uppercase bg-black/30 ${styles.text} border border-white/5`}>
                                Risk Level
                            </span>
                            <span className="text-slate-400 text-xs font-mono">ID: {assessment_id}</span>
                            {consensus_details && getConfidenceBadge(consensus_details.confidence_level)}
                        </div>
                        <h2 className={`text-5xl font-black ${styles.text} tracking-tight`}>
                            {risk_band || "UNKNOWN"}
                        </h2>
                    </div>

                    <div className="mt-8">
                        <div className="flex items-end gap-3 mb-2">
                            <span className="text-6xl font-light text-white">{probabilityPercent}%</span>
                            <span className="text-lg text-slate-400 mb-2">MRSA Probability</span>
                        </div>
                        <div className="h-3 w-full bg-black/40 rounded-full overflow-hidden backdrop-blur-sm">
                            <div
                                className={`h-full ${styles.indicator} transition-all duration-1000 ease-out`}
                                style={{ width: `${probabilityPercent}%` }}
                            ></div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Model Consensus & Agreement (Stage C.5) */}
            {consensus_details && (
                <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl overflow-hidden">
                    <button
                        onClick={() => setShowConsensus(!showConsensus)}
                        className="w-full flex items-center justify-between p-4 bg-white/5 hover:bg-white/10 transition-colors"
                    >
                        <div className="flex items-center gap-2 text-sm font-semibold text-slate-300">
                            <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                            Model Agreement Analysis
                        </div>
                        <svg className={`w-4 h-4 text-slate-500 transform transition-transform ${showConsensus ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                    </button>

                    {showConsensus && (
                        <div className="p-4 border-t border-white/10 animate-slide-down">
                            <div className="grid grid-cols-3 gap-2 mb-4">
                                {Object.entries(consensus_details.models).map(([key, model]) => {
                                    const labels = {
                                        rf: { title: "Primary Analysis", desc: "Balanced Clinical Model" },
                                        lr: { title: "Statistical Check", desc: "Baseline Linear Model" },
                                        xgb: { title: "Deep Pattern Scan", desc: "High-Sensitivity AI" }
                                    };
                                    const info = labels[key] || { title: key.toUpperCase(), desc: "Model" };

                                    return (
                                        <div key={key} className="bg-black/20 p-3 rounded-lg text-center border border-white/5">
                                            <div className="text-xs uppercase font-bold text-slate-400 mb-1">{info.title}</div>
                                            <div className={`text-lg font-bold ${model.band === 'RED' ? 'text-red-400' : model.band === 'AMBER' ? 'text-amber-400' : 'text-emerald-400'}`}>
                                                {(model.prob * 100).toFixed(0)}%
                                            </div>
                                            <div className="text-[10px] text-slate-500 mb-1">{model.band}</div>
                                            <div className="text-[9px] text-slate-600 border-t border-white/5 pt-1 mt-1">{info.desc}</div>
                                        </div>
                                    );
                                })}
                            </div>
                            {consensus_details.confidence_level !== 'HIGH' && (
                                <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg flex items-start gap-2 text-xs text-amber-200">
                                    <svg className="w-4 h-4 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                                    <div>
                                        <strong>Model Disagreement Detected.</strong><br />
                                        Models provided conflicting risk assessments. Standard clinical protocol is to adopt the safer (higher risk) or median approach. Clinical judgement advised.
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Recommendation Card */}
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-lg">
                <h3 className="text-xs uppercase tracking-wider font-semibold text-slate-400 mb-3 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    Stewardship Guidance
                </h3>
                <p className="text-xl font-medium text-slate-200 leading-relaxed">
                    {stewardship_message}
                </p>
            </div>

            {/* Action Area */}
            <div className="flex justify-center pt-2">
                <button
                    onClick={handleExplain}
                    disabled={explaining}
                    className="px-8 py-3 bg-white/10 hover:bg-white/15 border border-white/20 rounded-xl text-slate-200 font-medium transition-all hover:scale-105 active:scale-95 flex items-center gap-2"
                >
                    {explaining ? "Analyzing Models..." : "🔍 Explain Decision (SHAP)"}
                </button>
            </div>

            {/* Explanation / Error */}
            {explanation && (
                <div className="bg-slate-800/80 backdrop-blur-md p-6 rounded-2xl border border-slate-700/50 mt-4 animate-slide-up">
                    <h3 className="text-lg font-bold mb-4 text-white flex justify-between items-center">
                        Risk Factor Analysis
                        <span className="text-xs font-normal text-slate-400 bg-slate-700 px-2 py-1 rounded">Clinical Context (Primary Model)</span>
                    </h3>

                    <div className="space-y-4 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
                        {explanation.explanations.map((item, idx) => {
                            const isRisk = item.impact > 0;
                            const impactAbs = Math.abs(item.impact);
                            const barWidth = Math.min(100, (impactAbs / 0.25) * 100);

                            let intensity = "Low";
                            if (impactAbs > 0.15) intensity = "High";
                            else if (impactAbs > 0.05) intensity = "Moderate";

                            return (
                                <div key={idx} className="bg-white/5 rounded-xl p-3 border border-white/5">
                                    <div className="flex justify-between items-start mb-2">
                                        <div>
                                            <span className="block font-medium text-slate-200">{item.feature}</span>
                                            <span className="text-xs text-slate-500 font-mono">Value: {item.value}</span>
                                        </div>
                                        <div className={`text-right ${isRisk ? 'text-red-400' : 'text-emerald-400'}`}>
                                            <div className="text-xs font-bold uppercase tracking-wider">
                                                {isRisk ? "Increases Risk" : "Reduces Risk"}
                                            </div>
                                            <div className="text-xs opacity-70">{intensity} Impact</div>
                                        </div>
                                    </div>

                                    <div className="w-full h-1.5 bg-slate-700 rounded-full overflow-hidden flex">
                                        <div
                                            className={`h-full rounded-full ${isRisk ? 'bg-gradient-to-r from-red-600 to-red-400' : 'bg-gradient-to-r from-emerald-600 to-emerald-400'}`}
                                            style={{ width: `${barWidth}%` }}
                                        ></div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {error && <div className="text-center p-4 bg-red-900/30 border border-red-500/30 text-red-300 rounded-xl">{error}</div>}
        </div>
    );
};

export default MRSAResultPanel;
