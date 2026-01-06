import React, { useState } from 'react';
import { esblService } from '../../../services/esblService';

export const CaseRegistration = ({ onNext, isLoading }) => {
    const [formData, setFormData] = useState({
        Age: '',
        Gender: '',
        Ward: 'Medical',
        SpecimenSource: '', // Sample_Type
        CellCount: '',      // Cell_Count_Level
        PureGrowth: 'Pure',
        PusType: 'NA',
        Organism: '',
        Gram: 'GNB'         // Default to GNB per scope
    });

    const [scopeError, setScopeError] = useState(null);
    const [wardOptions, setWardOptions] = useState([]);
    const [sampleOptions, setSampleOptions] = useState([]);

    // Load Master Data on Mount
    React.useEffect(() => {
        const loadMasterData = async () => {
            const wards = await esblService.getMasterDefinitions('WARD');
            const samples = await esblService.getMasterDefinitions('SAMPLE_TYPE');

            setWardOptions(wards || []);
            setSampleOptions(samples || []);
        };
        loadMasterData();
    }, []);

    const checkScope = async () => {
        setScopeError(null);
        try {
            const result = await esblService.validateScope(formData.Organism, formData.Gram);
            if (!result.allowed) {
                setScopeError(result.reason);
                return false;
            }
            return true;
        } catch (e) {
            console.error(e);
            return false;
        }
    };

    const handleNext = async () => {
        if (!formData.Age || !formData.Organism || !formData.SpecimenSource || !formData.CellCount) {
            alert("Please complete all required fields.");
            return;
        }

        const isSafe = await checkScope();
        if (isSafe) {
            // Map UI keys to Backend Features
            const apiPayload = {
                Age: formData.Age,
                Gender: formData.Gender,
                Ward: formData.Ward,
                Sample_Type: formData.SpecimenSource,
                Cell_Count_Level: formData.CellCount,
                Pure_Growth: formData.PureGrowth,
                PUS_Type: formData.PusType,
                Organism: formData.Organism,
                Gram: formData.Gram
            };
            onNext(apiPayload);
        }
    };

    return (
        <div className="max-w-4xl mx-auto animate-fadeIn">
            {/* Steps Indicator */}
            <div className="flex items-center justify-between mb-8 px-8">
                <div className="flex flex-col items-center">
                    <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-sm shadow-lg shadow-blue-500/30">1</div>
                    <span className="text-xs font-bold text-slate-700 mt-2">Case Registration</span>
                </div>
                <div className="flex-1 h-0.5 bg-slate-200 mx-4"></div>
                <div className="flex flex-col items-center opacity-50">
                    <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-500 flex items-center justify-center font-bold text-sm">2</div>
                    <span className="text-xs font-bold text-slate-400 mt-2">Analysis</span>
                </div>
                <div className="flex-1 h-0.5 bg-slate-200 mx-4"></div>
                <div className="flex flex-col items-center opacity-50">
                    <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-500 flex items-center justify-center font-bold text-sm">3</div>
                    <span className="text-xs font-bold text-slate-400 mt-2">Action</span>
                </div>
            </div>

            <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
                <div className="p-8">
                    <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
                        <span>📋</span> Case Registration
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Section 1: Patient Demographics */}
                        <div className="space-y-6">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest border-b pb-2">Patient Demographics</h3>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-semibold text-slate-700 mb-1">Age</label>
                                    <div className="relative">
                                        <input
                                            type="number"
                                            className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none transition-all font-mono"
                                            placeholder="--"
                                            value={formData.Age}
                                            onChange={(e) => setFormData({ ...formData, Age: e.target.value })}
                                        />
                                        <span className="absolute right-3 top-3 text-xs text-slate-400 font-bold">YRS</span>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-slate-700 mb-1">Gender</label>
                                    <select
                                        className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg focus:border-blue-500 outline-none"
                                        value={formData.Gender}
                                        onChange={(e) => setFormData({ ...formData, Gender: e.target.value })}
                                    >
                                        <option value="">Select</option>
                                        <option value="Male">Male</option>
                                        <option value="Female">Female</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-1">Medical Unit / Ward</label>
                                <select
                                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg focus:border-blue-500 outline-none"
                                    value={formData.Ward}
                                    onChange={(e) => setFormData({ ...formData, Ward: e.target.value })}
                                >
                                    <option value="">Select Ward...</option>
                                    {wardOptions.length > 0 ? wardOptions.map(opt => (
                                        <option key={opt.id} value={opt.label}>{opt.label}</option>
                                    )) : (
                                        <>
                                            <option value="Medical">General Medical</option>
                                            <option value="Surgical">Surgical</option>
                                            <option value="ICU">ICU</option>
                                            <option value="Pediatric">Pediatric</option>
                                            <option value="Gyne">Gynecology/Obs</option>
                                            <option value="OPD">Outpatient (OPD)</option>
                                        </>
                                    )}
                                </select>
                            </div>
                        </div>

                        {/* Section 2: Microbiology Data */}
                        <div className="space-y-6">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest border-b pb-2">Specimen & Culture</h3>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-semibold text-slate-700 mb-1">Specimen (Sample)</label>
                                    <select
                                        className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg focus:border-blue-500 outline-none"
                                        value={formData.SpecimenSource}
                                        onChange={(e) => setFormData({ ...formData, SpecimenSource: e.target.value })}
                                    >
                                        <option value="">Select type...</option>
                                        {sampleOptions.length > 0 ? sampleOptions.map(opt => (
                                            <option key={opt.id} value={opt.label}>{opt.label}</option>
                                        )) : (
                                            <>
                                                <option value="Urine">Urine</option>
                                                <option value="Blood">Blood</option>
                                                <option value="Pus">Pus / Abscess</option>
                                                <option value="Wound">Wound Swab</option>
                                                <option value="BAL">BAL (Resp)</option>
                                                <option value="ET">ET Secretion</option>
                                            </>
                                        )}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-slate-700 mb-1">Cell Count</label>
                                    <select
                                        className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg focus:border-blue-500 outline-none"
                                        value={formData.CellCount}
                                        onChange={(e) => setFormData({ ...formData, CellCount: e.target.value })}
                                    >
                                        <option value="">Microscopy...</option>
                                        <option value="Low">Low (&lt;5/hpf)</option>
                                        <option value="Moderate">Moderate</option>
                                        <option value="High">High (&gt;25/hpf)</option>
                                    </select>
                                </div>
                            </div>

                            {(formData.SpecimenSource === 'Pus' || formData.SpecimenSource === 'Wound') && (
                                <div>
                                    <label className="block text-sm font-semibold text-slate-700 mb-1">Pus / Wound Type</label>
                                    <select
                                        className="w-full p-3 bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg focus:border-yellow-500 outline-none"
                                        value={formData.PusType}
                                        onChange={(e) => setFormData({ ...formData, PusType: e.target.value })}
                                    >
                                        <option value="NA">-- Not Applicable --</option>
                                        <option value="Abscess">Deep Abscess</option>
                                        <option value="Wound_Pus">Superficial Wound</option>
                                        <option value="ET_Secretion">ET Secretion (Map only if valid)</option>
                                    </select>
                                </div>
                            )}

                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-1">Isolated Organism</label>
                                <select
                                    className={`w-full p-3 border rounded-lg outline-none font-medium ${scopeError ? 'bg-red-50 border-red-300 text-red-700 animate-shake' : 'bg-slate-50 border-slate-200'
                                        }`}
                                    value={formData.Organism}
                                    onChange={(e) => {
                                        setFormData({ ...formData, Organism: e.target.value });
                                        if (scopeError) setScopeError(null);
                                    }}
                                >
                                    <option value="">Select Organism...</option>
                                    <option disabled className="bg-slate-100 italic">-- Enterobacterales (Supported) --</option>
                                    <option value="E_coli">Escherichia coli</option>
                                    <option value="Klebsiella_pneumoniae">Klebsiella pneumoniae</option>
                                    <option value="Enterobacter_spp">Enterobacter spp</option>
                                    {/* <option disabled className="bg-slate-100 italic">-- Out of Scope (Blocked) --</option>
                                    <option value="S_aureus">Staphylococcus aureus (MRSA)</option>
                                    <option value="P_aeruginosa">Pseudomonas aeruginosa</option>
                                    <option value="Acinetobacter">Acinetobacter baumannii</option> */}
                                </select>
                                {scopeError && (
                                    <div className="mt-2 text-xs font-bold text-red-600 flex items-center gap-1">
                                        <span>⛔</span> {scopeError}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="mt-8 flex justify-end">
                        <button
                            onClick={handleNext}
                            disabled={isLoading}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-bold text-lg shadow-lg shadow-blue-500/30 transition-all flex items-center gap-2"
                        >
                            {isLoading ? (
                                <>
                                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Analyzing...
                                </>
                            ) : (
                                <>
                                    Run Risk Assessment
                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
