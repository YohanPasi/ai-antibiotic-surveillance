import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const PostASTReview = ({ onReset, encounterId }) => {
    const [astPanel, setAstPanel] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [decisionLogged, setDecisionLogged] = useState(false);

    useEffect(() => {
        if (!encounterId) {
            setError("No Encounter ID provided");
            setLoading(false);
            return;
        }

        // Fetch actual lab results from database
        axios.get(`${API_URL}/esbl/lab-results/${encounterId}`)
            .then(response => {
                setAstPanel(response.data.results);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to load lab results:", err);
                setError("Failed to load lab results from database.");
                setLoading(false);
            });
    }, [encounterId]);

    // Dynamic Stewardship Logic
    const getStewardshipRecommendation = () => {
        if (!astPanel) return null;

        const tzpResult = astPanel['Pip-Tazo'] || astPanel['Piperacillin-Tazobactam'] || astPanel['TZP'];
        const meroResult = astPanel['Meropenem'];
        const ertaResult = astPanel['Ertapenem'];

        // Only recommend de-escalation if TZP is susceptible AND at least one carbapenem is susceptible
        const tzpSusceptible = tzpResult === 'S';
        const carbapenemAvailable = meroResult === 'S' || ertaResult === 'S';

        if (tzpSusceptible && carbapenemAvailable) {
            return {
                type: 'de-escalation',
                title: 'Stewardship Opportunity: De-Escalation Recommended',
                message: `The isolate is susceptible to Piperacillin-Tazobactam (TZP). If the patient is currently on a Carbapenem (${meroResult === 'S' ? 'Meropenem' : ''}${ertaResult === 'S' ? '/Ertapenem' : ''}), guidelines recommend de-escalating to TZP to preserve broad-spectrum efficacy.`,
                color: 'green'
            };
        } else if (!tzpSusceptible && carbapenemAvailable) {
            return {
                type: 'continue-carbapenem',
                title: 'Stewardship Note: Carbapenem Therapy Appropriate',
                message: `The isolate is resistant to Piperacillin-Tazobactam but susceptible to Carbapenems. Continue current therapy. No de-escalation opportunity at this time.`,
                color: 'blue'
            };
        } else if (tzpSusceptible && !carbapenemAvailable) {
            return {
                type: 'consider-tzp',
                title: 'Stewardship Note: Consider TZP Therapy',
                message: `The isolate is susceptible to Piperacillin-Tazobactam. If not already on TZP, consider switching from current regimen.`,
                color: 'yellow'
            };
        } else {
            return {
                type: 'limited-options',
                title: 'Alert: Limited Treatment Options',
                message: `The isolate shows resistance to both TZP and Carbapenems. Consider alternative agents (e.g., ${astPanel['Amikacin'] === 'S' ? 'Amikacin' : 'other aminoglycosides'}) or consult Infectious Disease.`,
                color: 'red'
            };
        }
    };

    const handleAcceptDeEscalation = () => {
        // Log the decision
        console.log("De-escalation accepted for encounter:", encounterId);

        // You could call an API endpoint here to log this decision
        // axios.post(`${API_URL}/esbl/stewardship-decision`, {
        //     encounter_id: encounterId,
        //     decision: 'accepted',
        //     recommendation_type: 'de-escalation'
        // });

        setDecisionLogged(true);
        alert("✅ De-escalation decision logged successfully!\n\nClinician has accepted the recommendation to switch to Piperacillin-Tazobactam.");
    };

    const handleKeepCurrentRegimen = () => {
        const reason = prompt("Please provide a reason for keeping the current regimen:\n\n(e.g., 'Patient improving on current therapy', 'Clinical instability', 'CNS infection requiring carbapenem')");

        if (reason) {
            console.log("Keeping current regimen. Reason:", reason);

            // Log to backend
            // axios.post(`${API_URL}/esbl/stewardship-decision`, {
            //     encounter_id: encounterId,
            //     decision: 'rejected',
            //     recommendation_type: 'de-escalation',
            //     reason: reason
            // });

            setDecisionLogged(true);
            alert("✅ Decision logged successfully!\n\nReason: " + reason);
        }
    };

    if (loading) {
        return (
            <div className="max-w-4xl mx-auto p-20 text-center">
                <div className="text-4xl mb-4">🔬</div>
                <p className="text-slate-500">Loading lab results...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="max-w-4xl mx-auto p-20 text-center">
                <div className="bg-red-50 border border-red-200 rounded-xl p-8">
                    <p className="text-red-700 font-bold">{error}</p>
                    <button onClick={onReset} className="mt-4 text-red-600 hover:underline">Go Back</button>
                </div>
            </div>
        );
    }

    const stewardshipRec = getStewardshipRecommendation();
    const colorMap = {
        green: { bg: 'bg-green-50', border: 'border-green-500', text: 'text-green-900', subtext: 'text-green-800', btn: 'bg-green-600 hover:bg-green-700', btnText: 'text-green-700' },
        blue: { bg: 'bg-blue-50', border: 'border-blue-500', text: 'text-blue-900', subtext: 'text-blue-800', btn: 'bg-blue-600 hover:bg-blue-700', btnText: 'text-blue-700' },
        yellow: { bg: 'bg-yellow-50', border: 'border-yellow-500', text: 'text-yellow-900', subtext: 'text-yellow-800', btn: 'bg-yellow-600 hover:bg-yellow-700', btnText: 'text-yellow-700' },
        red: { bg: 'bg-red-50', border: 'border-red-500', text: 'text-red-900', subtext: 'text-red-800', btn: 'bg-red-600 hover:bg-red-700', btnText: 'text-red-700' }
    };
    const colors = stewardshipRec ? colorMap[stewardshipRec.color] : colorMap['blue']; // Default to blue if no recommendation

    return (
        <div className="max-w-4xl mx-auto animate-fadeIn">
            {/* Header / Banner */}
            <div className="bg-slate-900 text-white rounded-t-2xl p-8 flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold flex items-center gap-3">
                        <span className="text-3xl">🔬</span> Confirmatory AST Review
                    </h2>
                    <p className="text-slate-400 mt-2">Laboratory results authorized by Microbiology.</p>
                    <p className="text-slate-500 text-sm mt-1 font-mono">Encounter: {encounterId}</p>
                </div>
                <div className="bg-red-500/20 border border-red-500/50 px-4 py-2 rounded-lg flex items-center gap-2">
                    <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                    <span className="text-xs font-bold uppercase tracking-wider text-red-100">Empiric AI Locked</span>
                </div>
            </div>

            <div className="bg-white border-x border-b border-slate-200 rounded-b-2xl p-8 space-y-8 shadow-sm">

                {/* 1. Dynamic Stewardship Feedback */}
                {stewardshipRec && (
                    <div className={`${colors.bg} border-l-4 ${colors.border} p-6 rounded-r-xl`}>
                        <h3 className={`font-bold ${colors.text} flex items-center gap-2`}>
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                            </svg>
                            {stewardshipRec.title}
                        </h3>
                        <p className={`${colors.subtext} mt-2 text-sm leading-relaxed`}>
                            {stewardshipRec.message}
                        </p>

                        {/* Action Buttons (only for de-escalation type) */}
                        {stewardshipRec.type === 'de-escalation' && !decisionLogged && (
                            <div className="mt-4 flex gap-3">
                                <button
                                    onClick={handleAcceptDeEscalation}
                                    className={`${colors.btn} text-white px-4 py-2 rounded-lg text-sm font-bold transition-colors shadow-sm`}
                                >
                                    Accept De-Escalation
                                </button>
                                <button
                                    onClick={handleKeepCurrentRegimen}
                                    className={`${colors.btnText} hover:underline text-sm font-medium`}
                                >
                                    Keep Current Regimen (Log Reason)
                                </button>
                            </div>
                        )}

                        {decisionLogged && (
                            <div className="mt-4 flex items-center gap-2 text-green-700">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                                </svg>
                                <span className="text-sm font-bold">Decision Logged</span>
                            </div>
                        )}
                    </div>
                )}

                {/* 2. AST Panel Grid */}
                <div>
                    <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                        <span className="text-lg">🧪</span> Susceptibility Panel
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {Object.entries(astPanel).map(([drug, result]) => {
                            const colorClass = result === 'S' ? 'bg-green-50 border-green-200 text-green-700' :
                                result === 'R' ? 'bg-red-50 border-red-200 text-red-700' :
                                    'bg-yellow-50 border-yellow-200 text-yellow-700';
                            const label = result === 'S' ? 'SUSCEPTIBLE' : result === 'R' ? 'RESISTANT' : 'INTERMEDIATE';

                            return (
                                <div key={drug} className={`${colorClass} border-2 rounded-xl p-6 text-center transition-all hover:shadow-md`}>
                                    <div className={`text-4xl font-bold mb-2 ${result === 'S' ? 'text-green-600' : result === 'R' ? 'text-red-600' : 'text-yellow-600'}`}>
                                        {result}
                                    </div>
                                    <div className="font-bold text-slate-800">{drug}</div>
                                    <div className={`text-xs font-medium mt-1 uppercase tracking-wider ${result === 'S' ? 'text-green-600' : result === 'R' ? 'text-red-600' : 'text-yellow-600'}`}>
                                        {label}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Footer */}
                <div className="pt-6 border-t border-slate-200 flex justify-between items-center">
                    <p className="text-xs text-slate-400">Result ID: {encounterId}</p>
                    <button onClick={onReset} className="text-slate-600 hover:text-slate-900 font-medium text-sm border border-slate-300 px-4 py-2 rounded-lg hover:bg-slate-50 transition-colors">
                        Start New Patient Encounter
                    </button>
                </div>
            </div>
        </div>
    );
};
