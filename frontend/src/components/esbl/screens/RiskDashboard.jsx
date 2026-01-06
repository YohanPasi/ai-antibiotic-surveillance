
import React from 'react';

export const RiskDashboard = ({ inputs, riskData, warnings, onNext, onBack }) => {
    const { probability, group, ood_warning } = riskData || {};

    // Dynamic Styles
    const isHigh = group === "High";
    const isLow = group === "Low";

    const colorClass = isHigh ? "bg-red-600" : isLow ? "bg-green-600" : "bg-yellow-500";
    const badgeClass = isHigh ? "bg-red-100 text-red-800" : isLow ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800";

    return (
        <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">

            {/* Steps Indicator (Optional - could be shared component, but hardcoded here for speed) */}
            <div className="flex items-center justify-center mb-8">
                <div className="flex items-center gap-3 opacity-50">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-200 text-slate-600 font-bold text-sm">1</span>
                    <span className="text-sm font-medium text-slate-500 uppercase tracking-wider">Registration</span>
                </div>
                <div className="w-16 h-0.5 bg-slate-200 mx-4"></div>
                <div className="flex items-center gap-3">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white font-bold text-sm ring-4 ring-blue-100">2</span>
                    <span className="text-sm font-semibold text-blue-900 uppercase tracking-wider">Analysis</span>
                </div>
                <div className="w-16 h-0.5 bg-slate-200 mx-4"></div>
                <div className="flex items-center gap-3 opacity-50">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-200 text-slate-600 font-bold text-sm">3</span>
                    <span className="text-sm font-medium text-slate-500 uppercase tracking-wider">Action</span>
                </div>
            </div>

            {/* SAFETY BANNERS */}
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
                <div className="bg-amber-100 text-amber-600 p-2 rounded-full shrink-0">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                </div>
                <div>
                    <h3 className="text-sm font-bold text-amber-900 uppercase tracking-wide">
                        Empiric Decision Support Only
                    </h3>
                    <p className="text-sm text-amber-700/80 mt-1 leading-relaxed">
                        Do not delay AST-guided therapy. This is a prediction based on surveillance data, not a definitive diagnosis.
                    </p>
                </div>
            </div>

            {ood_warning && (
                <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 flex items-center gap-4 animate-bounce-subtle shadow-sm shadow-purple-100">
                    <span className="text-2xl">📡</span>
                    <div className="flex-1">
                        <h3 className="text-sm font-bold text-purple-900">Out of Distribution Signal Detected</h3>
                        <p className="text-sm text-purple-700/80 mt-1">
                            The input parameters deviate from the training population. <strong>Model confidence may be reduced.</strong> Proceed with caution.
                        </p>
                    </div>
                </div>
            )}

            {/* ENCOUNTER ID BANNER */}
            {inputs.id && (
                <div className="bg-slate-900 text-white p-4 rounded-xl flex justify-between items-center shadow-lg">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-slate-800 rounded-lg">
                            <span className="text-xl">🆔</span>
                        </div>
                        <div>
                            <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Encounter ID</p>
                            <p className="text-xl font-mono font-bold tracking-widest">{inputs.id}</p>
                        </div>
                    </div>
                    <div className="text-xs text-slate-500 bg-slate-800 px-3 py-1 rounded border border-slate-700">
                        Copy for Lab Entry
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* LEFT: RISK SCORE CARD */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 flex flex-col items-center justify-center relative overflow-hidden">
                    <div className={`absolute top-0 inset-x-0 h-1 ${colorClass}`}></div>

                    <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-8">ESBL Infection Probability</h3>

                    <div className="relative">
                        {/* Outer Ring */}
                        <div className={`w-48 h-48 rounded-full border-8 border-slate-100 flex items-center justify-center`}>
                            {/* Inner "Gauge" - Simulated with color */}
                            <div className={`w-40 h-40 rounded-full flex flex-col items-center justify-center text-white shadow-xl transition-all duration-1000 ${colorClass}`}>
                                <span className="text-5xl font-bold tracking-tighter">{(probability * 100).toFixed(1)}%</span>
                                <span className="text-xs font-medium uppercase opacity-90 mt-1">Confidence Score</span>
                            </div>
                        </div>
                    </div>

                    <div className="mt-8 text-center space-y-2">
                        <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-bold uppercase tracking-wider ${badgeClass}`}>
                            <span className="w-2 h-2 rounded-full bg-current"></span>
                            {group} Risk Group
                        </div>
                        <p className="text-slate-400 text-xs text-center max-w-xs mx-auto">
                            Based on local epidemiology and patient factors.
                        </p>
                    </div>
                </div>

                {/* RIGHT: CONTEXT CARD */}
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 flex flex-col">
                    <div className="flex items-center justify-between mb-6 border-b border-slate-100 pb-4">
                        <h3 className="text-slate-800 text-lg font-bold">Case Context</h3>
                        <span className="text-xs font-mono text-slate-400">INPUT SUMMARY</span>
                    </div>

                    <dl className="space-y-4 text-sm flex-1">
                        <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                            <dt className="text-slate-500 font-medium">Patient Age</dt>
                            <dd className="font-bold text-slate-900">{inputs.Age} <span className="text-slate-400 font-normal text-xs">YRS</span></dd>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                            <dt className="text-slate-500 font-medium">Ward Location</dt>
                            <dd className="font-bold text-slate-900">{inputs.Ward}</dd>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                            <dt className="text-slate-500 font-medium">Organism</dt>
                            <dd className="font-bold text-slate-900 italic">{inputs.Organism.replace(/_/g, " ")}</dd>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg border border-slate-100">
                            <dt className="text-slate-500 font-medium">Specimen Source</dt>
                            <dd className="font-bold text-slate-900">{inputs.Sample_Type}</dd>
                        </div>
                    </dl>

                    <div className="mt-8 pt-4 border-t border-slate-100 flex justify-between items-center text-xs text-slate-400 font-medium">
                        <span>Model: XGB-Early-v1</span>
                        <span>{Object.keys(inputs).length} Features Processed</span>
                    </div>
                </div>
            </div>

            <div className="flex justify-between pt-4">
                <button
                    onClick={onBack}
                    className="flex items-center gap-2 text-slate-500 hover:text-slate-800 font-medium px-4 py-2 rounded-lg hover:bg-slate-100 transition-colors"
                >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                    Adjust Inputs
                </button>
                <button
                    onClick={onNext}
                    className="group relative inline-flex items-center justify-center px-8 py-3 font-semibold text-white transition-all duration-200 bg-slate-900 rounded-xl hover:bg-slate-800 hover:shadow-lg hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900"
                >
                    View Antibiotic Recommendations
                    <svg className="w-4 h-4 ml-2 transition-transform duration-200 group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                </button>
            </div>
        </div>
    );
};
