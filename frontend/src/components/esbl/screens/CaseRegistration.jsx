
import React, { useState } from 'react';
import { esblService } from '../../../services/esblService';

export const CaseRegistration = ({ onNext, isLoading }) => {
    const [form, setForm] = useState({
        Age: '',
        Ward: 'ICU',
        Sample_Type: 'Urine',
        Organism: 'E_coli',
        Gram: 'GNB'
    });

    const [scopeError, setScopeError] = useState(null);

    const handleChange = (e) => {
        setForm({ ...form, [e.target.name]: e.target.value });
        setScopeError(null);
    };

    const validateAndProceed = async () => {
        if (!form.Age || !form.Organism) {
            setScopeError("Please fill all fields.");
            return;
        }

        // Stage 8 PRO-ACTIVE CHECK
        try {
            const validation = await esblService.validateScope(form.Organism, form.Gram);
            if (!validation.allowed) {
                setScopeError(`SCOPE VIOLATION: ${validation.reason}`);
                return;
            }

            // If valid, proceed to Engine
            onNext(form);

        } catch (e) {
            setScopeError("Validation Service Unavailable.");
        }
    };

    return (
        <div className="max-w-3xl mx-auto">
            {/* Progress / Step Header */}
            <div className="mb-8 flex items-center justify-center">
                <div className="flex items-center gap-3">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-600 text-white font-bold text-sm ring-4 ring-blue-100">1</span>
                    <span className="text-sm font-semibold text-blue-900 uppercase tracking-wider">Case Registration</span>
                </div>
                <div className="w-16 h-0.5 bg-slate-200 mx-4"></div>
                <div className="flex items-center gap-3 opacity-50">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-200 text-slate-600 font-bold text-sm">2</span>
                    <span className="text-sm font-medium text-slate-500 uppercase tracking-wider">Analysis</span>
                </div>
                <div className="w-16 h-0.5 bg-slate-200 mx-4"></div>
                <div className="flex items-center gap-3 opacity-50">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-slate-200 text-slate-600 font-bold text-sm">3</span>
                    <span className="text-sm font-medium text-slate-500 uppercase tracking-wider">Action</span>
                </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="bg-slate-50 border-b border-slate-200 px-8 py-4 flex justify-between items-center">
                    <h2 className="font-semibold text-slate-800">New Patient Encounter</h2>
                    <span className="text-xs font-mono text-slate-400 bg-white px-2 py-1 rounded border border-slate-200">ID: {Math.random().toString(36).substr(2, 9).toUpperCase()}</span>
                </div>

                <div className="p-8 space-y-8">
                    {/* Section 1: Demographics */}
                    <div>
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                            <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                            Patient Demographics
                        </h3>
                        <div className="grid grid-cols-2 gap-6">
                            <div className="group">
                                <label className="block text-sm font-medium text-slate-700 mb-2 transition-colors group-focus-within:text-blue-600">Patient Age (Years)</label>
                                <div className="relative">
                                    <input
                                        type="number"
                                        name="Age"
                                        value={form.Age}
                                        onChange={handleChange}
                                        className="w-full pl-4 pr-12 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none text-slate-900 font-medium placeholder:text-slate-300"
                                        placeholder="e.g. 55"
                                    />
                                    <span className="absolute right-4 top-3.5 text-xs font-bold text-slate-400 pointer-events-none">YRS</span>
                                </div>
                            </div>
                            <div className="group">
                                <label className="block text-sm font-medium text-slate-700 mb-2 transition-colors group-focus-within:text-blue-600">Clinical Ward</label>
                                <div className="relative">
                                    <select
                                        name="Ward"
                                        value={form.Ward}
                                        onChange={handleChange}
                                        className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none text-slate-900 font-medium appearance-none bg-white"
                                    >
                                        <option value="ICU">ICU (Intensive Care)</option>
                                        <option value="Medical">General Medical</option>
                                        <option value="Surgical">Surgical Unit</option>
                                    </select>
                                    <div className="absolute right-4 top-4 pointer-events-none text-slate-400">
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="h-px bg-slate-100 w-full"></div>

                    {/* Section 2: Microbiology */}
                    <div>
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                            <span className="w-2 h-2 bg-purple-400 rounded-full"></span>
                            Microbiology Data
                        </h3>
                        <div className="grid grid-cols-2 gap-6">
                            <div className="group">
                                <label className="block text-sm font-medium text-slate-700 mb-2 transition-colors group-focus-within:text-purple-600">Identified Organism</label>
                                <div className="relative">
                                    <select
                                        name="Organism"
                                        value={form.Organism}
                                        onChange={handleChange}
                                        className="w-full px-4 py-3 border border-yellow-200 bg-yellow-50/50 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all outline-none text-slate-900 font-medium appearance-none"
                                    >
                                        <option value="E_coli">Escherichia coli</option>
                                        <option value="Klebsiella_pneumoniae">Klebsiella pneumoniae</option>
                                        <option value="Staphylococcus_aureus">⚠️ Staphylococcus aureus (Control)</option>
                                        <option value="Pseudomonas_aeruginosa">⚠️ Pseudomonas aeruginosa (OOD)</option>
                                    </select>
                                    <div className="absolute right-4 top-4 pointer-events-none text-yellow-600/50">
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                                    </div>
                                </div>
                            </div>
                            <div className="group">
                                <label className="block text-sm font-medium text-slate-700 mb-2 transition-colors group-focus-within:text-purple-600">Gram Stain</label>
                                <div className="relative">
                                    <select
                                        name="Gram"
                                        value={form.Gram}
                                        onChange={handleChange}
                                        className="w-full px-4 py-3 border border-yellow-200 bg-yellow-50/50 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all outline-none text-slate-900 font-medium appearance-none"
                                    >
                                        <option value="GNB">Gram Negative Bacilli (GNB)</option>
                                        <option value="GPC">Gram Positive Cocci (GPC)</option>
                                    </select>
                                    <div className="absolute right-4 top-4 pointer-events-none text-yellow-600/50">
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Alerts Area */}
                    <div className="space-y-3">
                        {scopeError ? (
                            <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 animate-shake">
                                <div className="bg-red-100 p-2 rounded-full shrink-0 mt-0.5">
                                    <span className="text-xl">⛔</span>
                                </div>
                                <div>
                                    <h4 className="text-sm font-bold text-red-800">Scope Violation</h4>
                                    <p className="text-sm text-red-600 mt-1">{scopeError}</p>
                                </div>
                            </div>
                        ) : (
                            <div className="flex gap-3 p-4 bg-blue-50/50 border border-blue-100 rounded-xl">
                                <div className="shrink-0 mt-0.5 text-blue-500">
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                </div>
                                <p className="text-sm text-blue-700/80 leading-relaxed">
                                    <strong>Clinical Note:</strong> This module is calibrated exclusively for <em>Enterobacterales</em>. Ensure input data reflects the latest lab report.
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Action Bar */}
                    <div className="pt-4 flex justify-end items-center gap-4">
                        <button className="text-slate-400 text-sm font-medium hover:text-slate-600 transition-colors">Clear Form</button>
                        <button
                            onClick={validateAndProceed}
                            disabled={isLoading}
                            className={`
                                relative overflow-hidden bg-slate-900 text-white px-8 py-3.5 rounded-xl font-medium shadow-lg shadow-slate-900/20 
                                transition-all duration-200 hover:bg-slate-800 hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0 active:scale-95 disabled:opacity-50 disabled:pointer-events-none
                                flex items-center gap-2
                            `}
                        >
                            {isLoading ? (
                                <>
                                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                    Validating Metadata...
                                </>
                            ) : (
                                <>
                                    Run Risk Assessment
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
