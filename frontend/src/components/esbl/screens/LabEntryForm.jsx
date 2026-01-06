import React, { useState } from 'react';
import { Search, FlaskConical, Save, AlertCircle, FileText, Shield } from 'lucide-react';
import { esblService } from '../../../services/esblService';

export const LabEntryForm = ({ onSubmit }) => {
    const [searchId, setSearchId] = useState('');
    const [foundCase, setFoundCase] = useState(null);
    const [error, setError] = useState(null);
    const [astData, setAstData] = useState({
        "Amikacin": "S",
        "Gentamicin": "S",
        "Meropenem": "S",
        "Ertapenem": "S",
        "Ceftriaxone": "R",
        "Cefepime": "R",
        "Pip-Tazo": "S",
        "Ciprofloxacin": "R"
    });

    const handleSearch = async (e) => {
        e.preventDefault();
        setError(null);

        // Fetch from Real Backend Service
        try {
            const record = await esblService.getEncounter(searchId);

            if (record) {
                setFoundCase(record);
            } else {
                setFoundCase(null);
                setError("Encounter ID not found.");
            }
        } catch (err) {
            setError("Error retrieving case.");
        }
    };

    const handleSave = () => {
        if (!foundCase) return;
        onSubmit(foundCase.inputs.id, astData, foundCase.inputs);
    };

    return (
        <div className="max-w-6xl mx-auto animate-fadeIn p-6">
            <h1 className="text-3xl font-bold text-slate-900 mb-8 flex items-center gap-3">
                <div className="p-3 bg-purple-100 rounded-xl text-purple-600">
                    <FlaskConical className="w-8 h-8" />
                </div>
                <div>
                    <span>Microbiology Lab Entry</span>
                    <p className="text-sm font-normal text-slate-500 mt-1">Enter susceptibility results to validate AI predictions.</p>
                </div>
            </h1>

            {/* Search Section */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 mb-8">
                <form onSubmit={handleSearch} className="flex gap-4 items-end max-w-lg">
                    <div className="flex-1">
                        <label className="block text-sm font-bold text-slate-700 mb-2">Scan / Enter Encounter ID</label>
                        <div className="relative">
                            <input
                                type="text"
                                value={searchId}
                                onChange={(e) => setSearchId(e.target.value.toUpperCase())}
                                placeholder="ENC-XXXXXX"
                                className="w-full pl-11 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-purple-500/50 outline-none font-mono text-lg font-bold tracking-wider uppercase transition-all"
                            />
                            <Search className="w-6 h-6 text-slate-400 absolute left-3.5 top-4" />
                        </div>
                    </div>
                    <button type="submit" className="bg-slate-900 hover:bg-slate-800 text-white px-8 py-4 rounded-xl font-bold transition-all shadow-lg shadow-slate-900/20 active:scale-95">
                        Find Case
                    </button>
                </form>
                {error && (
                    <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-xl flex items-center gap-2 border border-red-100">
                        <AlertCircle className="w-5 h-5" />
                        <span className="font-medium">{error}</span>
                    </div>
                )}
            </div>

            {/* Results Grid - Only visible if found */}
            {foundCase && (
                <div className="animate-slideUp space-y-8">

                    {/* INFO GRID */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* 1. Patient Context */}
                        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col">
                            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <FileText className="w-4 h-4" /> Case Details
                            </h3>
                            <div className="space-y-4 flex-1">
                                <div className="flex justify-between border-b border-slate-100 pb-2">
                                    <span className="text-slate-500">Patient Age</span>
                                    <span className="font-bold text-slate-900">{foundCase.inputs.Age} Yrs ({foundCase.inputs.Gender})</span>
                                </div>
                                <div className="flex justify-between border-b border-slate-100 pb-2">
                                    <span className="text-slate-500">Ward</span>
                                    <span className="font-bold text-slate-900">{foundCase.inputs.Ward}</span>
                                </div>
                                <div className="flex justify-between border-b border-slate-100 pb-2">
                                    <span className="text-slate-500">Specimen</span>
                                    <span className="font-bold text-slate-900">{foundCase.inputs.Sample_Type} ({foundCase.inputs.Cell_Count_Level})</span>
                                </div>
                                <div className="flex justify-between pt-2">
                                    <span className="text-slate-500">Organism</span>
                                    <span className="font-bold text-slate-900 italic">{foundCase.inputs.Organism.replace(/_/g, " ")}</span>
                                </div>
                            </div>
                        </div>

                        {/* 2. AI Prediction Recap */}
                        <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200 shadow-inner flex flex-col">
                            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <Shield className="w-4 h-4" /> AI Prediction Recap
                            </h3>
                            <div className="flex items-center gap-4 mb-6">
                                <div className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-bold text-xl shadow-lg
                                    ${foundCase.result.risk.group === 'High' ? 'bg-red-500' : 'bg-green-500'}`}>
                                    {(foundCase.result.risk.probability * 100).toFixed(0)}%
                                </div>
                                <div>
                                    <div className="text-2xl font-bold text-slate-900">{foundCase.result.risk.group} Risk</div>
                                    <div className="text-sm text-slate-500">ESBL Positivity Probability</div>
                                </div>
                            </div>
                            <div className="bg-white rounded-xl p-4 border border-slate-200">
                                <div className="text-xs font-bold text-slate-400 uppercase mb-2">Top Recommendation</div>
                                <div className="font-bold text-slate-800 text-lg">
                                    {foundCase.result.recommendations[0].drug}
                                </div>
                                <div className="text-sm text-green-600 font-medium">
                                    {(foundCase.result.recommendations[0].success_prob * 100).toFixed(0)}% Predicted Efficacy
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* AST INPUT CARD */}
                    <div className="bg-white rounded-2xl shadow-lg border border-purple-100 overflow-hidden">
                        <div className="bg-purple-50 px-8 py-6 border-b border-purple-100">
                            <h3 className="text-lg font-bold text-purple-900">Enter Verified Susceptibility Results</h3>
                            <p className="text-purple-600 text-sm">Input data from the VITEK/Phoenix machine report.</p>
                        </div>

                        <div className="p-8">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                                {Object.keys(astData).map((drug) => (
                                    <div key={drug} className="bg-slate-50 p-4 rounded-xl border border-slate-200 hover:border-purple-200 transition-colors">
                                        <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 truncate" title={drug}>{drug}</label>
                                        <select
                                            value={astData[drug]}
                                            onChange={(e) => setAstData({ ...astData, [drug]: e.target.value })}
                                            className={`w-full p-3 rounded-lg border-2 font-bold text-center outline-none transition-all ${astData[drug] === 'S' ? 'bg-green-50 text-green-700 border-green-200 focus:border-green-500' :
                                                astData[drug] === 'R' ? 'bg-red-50 text-red-700 border-red-200 focus:border-red-500' :
                                                    'bg-yellow-50 text-yellow-700 border-yellow-200 focus:border-yellow-500'
                                                }`}
                                        >
                                            <option value="S">S (Sensitive)</option>
                                            <option value="I">I (Intermediate)</option>
                                            <option value="R">R (Resistant)</option>
                                        </select>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-8 flex justify-end pt-6 border-t border-slate-100">
                                <button
                                    onClick={handleSave}
                                    className="bg-purple-600 hover:bg-purple-700 text-white px-10 py-4 rounded-xl font-bold shadow-xl shadow-purple-600/30 flex items-center gap-3 transition-transform active:scale-95"
                                >
                                    <Save className="w-5 h-5" />
                                    Submit Results & Trigger Review
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
