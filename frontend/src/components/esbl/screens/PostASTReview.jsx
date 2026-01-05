import React, { useState } from 'react';

export const PostASTReview = ({ onReset }) => {
    // Simulated AST Panel for Demo
    const astPanel = {
        "Amikacin": "S",
        "Gentamicin": "S",
        "Meropenem": "S",
        "Ertapenem": "S",
        "Ceftriaxone": "R",
        "Cefepime": "R",
        "Pip-Tazo": "S", // Key for de-escalation
        "Ciprofloxacin": "R"
    };

    return (
        <div className="max-w-4xl mx-auto animate-fadeIn">
            {/* Header / Banner */}
            <div className="bg-slate-900 text-white rounded-t-2xl p-8 flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold flex items-center gap-3">
                        <span className="text-3xl">🔬</span> Confirmatory AST Review
                    </h2>
                    <p className="text-slate-400 mt-2">Laboratory results authorized by Microbiology.</p>
                </div>
                <div className="bg-red-500/20 border border-red-500/50 px-4 py-2 rounded-lg flex items-center gap-2">
                    <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                    <span className="text-xs font-bold uppercase tracking-wider text-red-100">Empiric AI Locked</span>
                </div>
            </div>

            <div className="bg-white border-x border-b border-slate-200 rounded-b-2xl p-8 space-y-8 shadow-sm">

                {/* 1. Stewardship Feedback */}
                <div className="bg-green-50 border-l-4 border-green-500 p-6 rounded-r-xl">
                    <h3 className="font-bold text-green-900 flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                        Stewardship Opportunity: De-Escalation Recommended
                    </h3>
                    <p className="text-green-800 mt-2 text-sm leading-relaxed">
                        The isolate is susceptible to <strong>Piperacillin-Tazobactam (TZP)</strong>.
                        If the patient is currently on a Carbapenem (Meropenem/Ertapenem), guidelines recommend de-escalating to TZP to preserve broad-spectrum efficacy.
                    </p>
                    <div className="mt-4 flex gap-3">
                        <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-bold transition-colors shadow-sm">
                            Accept De-Escalation
                        </button>
                        <button className="text-green-700 hover:underline text-sm font-medium">
                            Keep Current Regimen (Log Reason)
                        </button>
                    </div>
                </div>

                {/* 2. AST Panel Grid */}
                <div>
                    <h3 className="text-slate-800 font-bold mb-4 flex items-center gap-2">
                        <span>🧪</span> Susceptibility Panel
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {Object.entries(astPanel).map(([drug, result]) => (
                            <div key={drug} className={`p-4 rounded-xl border flex flex-col items-center justify-center text-center ${result === 'S' ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'
                                }`}>
                                <span className={`text-2xl font-black ${result === 'S' ? 'text-green-600' : 'text-red-500'}`}>
                                    {result}
                                </span>
                                <span className="text-sm font-bold text-slate-700 mt-1">{drug}</span>
                                <span className="text-xs text-slate-500 uppercase tracking-widest mt-1">
                                    {result === 'S' ? 'Susceptible' : 'Resistant'}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* 3. Action Footer */}
                <div className="border-t pt-8 flex justify-between items-center">
                    <div className="text-xs text-slate-400">
                        Result ID: {Math.random().toString(36).substr(2, 12).toUpperCase()} <br />
                        Authorized: Just now
                    </div>
                    <button
                        onClick={onReset}
                        className="text-slate-500 hover:text-slate-800 font-medium px-4 py-2"
                    >
                        Start New Patient Encounter
                    </button>
                </div>

            </div>
        </div>
    );
};
