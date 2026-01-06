
import React, { useState } from 'react';

export const RecommendationEngine = ({ recommendations, riskGroup, onOverride, astLocked, encounterId }) => {
    const [selectedDrug, setSelectedDrug] = useState(null);
    const [showOverrideModal, setShowOverrideModal] = useState(false);

    if (astLocked) {
        return (
            <div className="max-w-4xl mx-auto h-96 flex flex-col items-center justify-center bg-slate-50 rounded-2xl border-2 border-slate-200 border-dashed animate-fadeIn">
                <div className="bg-slate-100 p-6 rounded-full mb-6">
                    <span className="text-6xl">🔒</span>
                </div>
                <h2 className="text-2xl font-bold text-slate-800">Empiric Guide Locked</h2>
                <p className="text-slate-500 mt-2 max-w-md text-center">
                    Confirmatory AST results have been uploaded. The probabilistic engine is disabled to prevent conflicting guidance.
                </p>
                <button className="mt-8 bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors">
                    View AST Panel
                </button>
            </div>
        )
    }

    return (
        <div className="max-w-5xl mx-auto animate-fadeIn">
            {/* Steps Indicator */}
            <div className="flex items-center justify-center mb-10">
                <div className="flex items-center gap-3 opacity-50">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-200 text-slate-600 font-bold text-sm">1</span>
                </div>
                <div className="w-16 h-0.5 bg-slate-200 mx-4"></div>
                <div className="flex items-center gap-3 opacity-50">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-200 text-slate-600 font-bold text-sm">2</span>
                </div>
                <div className="w-16 h-0.5 bg-slate-200 mx-4"></div>
                <div className="flex items-center gap-3">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white font-bold text-sm ring-4 ring-blue-100">3</span>
                    <span className="text-sm font-semibold text-blue-900 uppercase tracking-wider">Action</span>
                </div>
            </div>

            {/* ENCOUNTER ID BANNER */}
            {encounterId && (
                <div className="bg-slate-900 text-white p-4 rounded-xl flex justify-between items-center shadow-lg mb-8">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-slate-800 rounded-lg">
                            <span className="text-xl">🆔</span>
                        </div>
                        <div>
                            <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Encounter ID</p>
                            <p className="text-xl font-mono font-bold tracking-widest">{encounterId}</p>
                        </div>
                    </div>
                </div>
            )}

            <div className="flex items-center justify-between mb-8">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900">Empiric Therapy Guide</h2>
                    <p className="text-slate-500 text-sm mt-1">AI-Ranked Antibiotic Recommendations</p>
                </div>
                <div className={`px-4 py-2 rounded-xl border flex items-center gap-3 ${riskGroup === 'High' ? 'bg-red-50 border-red-100 text-red-800' : 'bg-green-50 border-green-100 text-green-800'}`}>
                    <span className="text-xs font-bold uppercase tracking-wider">Active Strategy:</span>
                    <span className="font-bold">{riskGroup === 'High' ? 'ESCALATION (Safety First)' : 'SPARING (Stewardship First)'}</span>
                </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden mb-8">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-slate-50/80 border-b border-slate-200 text-xs font-bold uppercase text-slate-400 tracking-wider">
                            <th className="p-5 w-20 text-center">Rank</th>
                            <th className="p-5">Antibiotic Agent</th>
                            <th className="p-5 w-48">Predicted Efficacy</th>
                            <th className="p-5">Stewardship Note</th>
                            <th className="p-5 text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {recommendations.map((rec, index) => (
                            <tr key={rec.drug} className={`group transition-all hover:bg-slate-50/80 ${index === 0 ? 'bg-blue-50/30' : ''}`}>
                                <td className="p-5">
                                    <span className={`mx-auto flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm shadow-sm ${index === 0 ? 'bg-blue-600 text-white ring-4 ring-blue-50' : 'bg-white text-slate-500 border border-slate-200'}`}>
                                        {index + 1}
                                    </span>
                                </td>
                                <td className="p-5">
                                    <div className="font-bold text-slate-900 text-base">{rec.drug}</div>
                                    <div className="text-xs text-slate-400 font-medium mt-0.5">Beta-lactam / Example Class</div>
                                </td>
                                <td className="p-5">
                                    <div className="space-y-1.5">
                                        <div className="flex justify-between text-xs font-bold">
                                            <span className={rec.success_prob > 0.9 ? 'text-green-700' : 'text-slate-700'}>Likely Susceptible</span>
                                            <span className="text-slate-500">{(rec.success_prob * 100).toFixed(0)}%</span>
                                        </div>
                                        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full rounded-full ${rec.success_prob > 0.9 ? 'bg-green-500' : rec.success_prob > 0.7 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                                style={{ width: `${rec.success_prob * 100}%` }}
                                            />
                                        </div>
                                    </div>
                                </td>
                                <td className="p-5">
                                    {rec.stewardship_note === 'Restricted' ? (
                                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-amber-50 text-amber-700 border border-amber-100">
                                            <span>⚠️</span> Restricted
                                        </span>
                                    ) : (
                                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold bg-green-50 text-green-700 border border-green-100">
                                            <span>✅</span> Preferred
                                        </span>
                                    )}
                                </td>
                                <td className="p-5 text-right">
                                    <button className="text-sm font-semibold text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-4 py-2 rounded-lg transition-colors">
                                        Select
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="bg-slate-50 rounded-xl border border-dashed border-slate-300 p-6 flex items-center justify-between">
                <div>
                    <h4 className="text-sm font-bold text-slate-800">Clinical Disagreement?</h4>
                    <p className="text-sm text-slate-500 mt-1">If you choose to deviate from these recommendations, a reason code is required for the audit log.</p>
                </div>
                <button
                    onClick={() => setShowOverrideModal(true)}
                    className="flex items-center gap-2 text-sm font-bold text-slate-700 bg-white border border-slate-300 px-4 py-2.5 rounded-lg hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-sm"
                >
                    <span>✏️</span>
                    Log Override Decision
                </button>
            </div>
        </div>
    );
};
