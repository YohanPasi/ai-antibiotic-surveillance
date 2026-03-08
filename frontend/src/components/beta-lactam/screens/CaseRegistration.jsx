import React, { useState, useEffect } from 'react';
import { Stethoscope, AlertTriangle, ChevronRight, Activity, Beaker } from 'lucide-react';
import { betaLactamService } from '../../../services/betaLactamService';

const CaseRegistration = ({ onComplete }) => {
    const [formData, setFormData] = useState({
        Age: '',
        Gender: '',
        Ward: '',
        Organism: '',
        Sample_Type: '',
        Cell_Count_Level: '',
        PUS_Type: 'NA',
        Pure_Growth: 'Pure'
    });

    const [loading, setLoading] = useState(false);
    const [scopeError, setScopeError] = useState(null);
    const [wardOptions, setWardOptions] = useState([]);
    const [sampleOptions, setSampleOptions] = useState([]);

    // Fetch master data on component mount
    useEffect(() => {
        const loadMasterData = async () => {
            try {
                const [wards, samples] = await Promise.all([
                    betaLactamService.getMasterDefinitions('WARD'),
                    betaLactamService.getMasterDefinitions('SAMPLE_TYPE')
                ]);

                console.log("Master data successfully loaded. Wards length:", wards.length, "Samples length:", samples.length);
                if (wards.length > 0) {
                    console.log("First ward item structure:", wards[0]);
                }

                // Fallbacks in case API returns empty lists
                setWardOptions(wards.length > 0 ? wards : [
                    { id: '1', value: 'Medical', label: 'Medical' },
                    { id: '2', value: 'Surgical', label: 'Surgical' },
                    { id: '3', value: 'ICU', label: 'ICU' },
                    { id: '4', value: 'Pediatric', label: 'Pediatric' },
                    { id: '5', value: 'Gyne', label: 'Gynecology/Obstetrics' },
                    { id: '6', value: 'OPD', label: 'OPD/Emergency' }
                ]);

                setSampleOptions(samples.length > 0 ? samples : [
                    { id: '1', value: 'Urine', label: 'Urine' },
                    { id: '2', value: 'Blood', label: 'Blood' },
                    { id: '3', value: 'Pus', label: 'Pus / Swab' },
                    { id: '4', value: 'Wound', label: 'Wound' },
                    { id: '5', value: 'BAL', label: 'BAL / Sputum' },
                    { id: '6', value: 'ET', label: 'ET Secretion' }
                ]);
            } catch (err) {
                console.warn("Failed to load master data, using fallbacks");
                setWardOptions([
                    { id: '1', value: 'Medical', label: 'Medical' },
                    { id: '2', value: 'Surgical', label: 'Surgical' },
                    { id: '3', value: 'ICU', label: 'ICU' },
                    { id: '4', value: 'Pediatric', label: 'Pediatric' },
                    { id: '5', value: 'Gyne', label: 'Gynecology/Obstetrics' },
                    { id: '6', value: 'OPD', label: 'OPD/Emergency' }
                ]);
                setSampleOptions([
                    { id: '1', value: 'Urine', label: 'Urine' },
                    { id: '2', value: 'Blood', label: 'Blood' },
                    { id: '3', value: 'Pus', label: 'Pus / Swab' },
                    { id: '4', value: 'Wound', label: 'Wound' },
                    { id: '5', value: 'BAL', label: 'BAL / Sputum' },
                    { id: '6', value: 'ET', label: 'ET Secretion' }
                ]);
            }
        };

        loadMasterData();
    }, []);

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        // Clear scope error when organism changes
        if (field === 'Organism') setScopeError(null);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!formData.Age || !formData.Organism || !formData.Sample_Type || !formData.Cell_Count_Level) {
            alert("Please fill in all required fields (Age, Organism, Specimen, Cell Count)");
            return;
        }

        setLoading(true);
        setScopeError(null);

        try {
            // Stage 8 Governance: Scope Check
            const scopeCheck = await betaLactamService.validateScope(formData.Organism, 'GNB');

            if (!scopeCheck.allowed) {
                setScopeError(scopeCheck.reason);
                setLoading(false);
                return;
            }

            // Map frontend fields to the format expected by the model inputs
            const mappedInputs = {
                Age: formData.Age,
                Gender: formData.Gender,
                Ward: formData.Ward,
                Organism: formData.Organism,
                Gram: 'GNB', // Hardcoded per UI scope
                Sample_Type: formData.Sample_Type,
                Cell_Count_Level: formData.Cell_Count_Level,
                PUS_Type: (formData.Sample_Type === 'Pus' || formData.Sample_Type === 'Wound') ? formData.PUS_Type : 'NA',
                Pure_Growth: formData.Pure_Growth
            };

            onComplete(mappedInputs);
        } catch (err) {
            setScopeError("Failed to validate scope. Please ensure backend is reachable.");
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in zoom-in-95 duration-300">
            {/* Header section untouched layout, updated text for Beta-Lactam */}
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-slate-200 dark:border-white/10 p-6 flex items-start gap-4">
                <div className="p-3 bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 rounded-lg shrink-0">
                    <Stethoscope className="w-6 h-6" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Patient Case Registration</h2>
                    <p className="text-slate-500 dark:text-gray-400 mt-1">
                        Enter patient demographics and microscopy data. The clinical system will assess
                        susceptibility across all beta-lactam generations.
                    </p>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-slate-200 dark:border-white/10 divide-y divide-slate-100 dark:divide-white/5">
                {/* Section A: Demographics */}
                <div className="p-6 space-y-4">
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-gray-400 flex items-center gap-2">
                        <Activity className="w-4 h-4" />
                        Section A: Demographics
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700 dark:text-gray-300">Patient Age <span className="text-red-500">*</span></label>
                            <div className="relative">
                                <input
                                    type="number"
                                    min="0"
                                    max="120"
                                    value={formData.Age}
                                    onChange={(e) => handleChange('Age', e.target.value)}
                                    className="w-full rounded-lg border-slate-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white pl-4 pr-12 py-2.5 focus:border-blue-500 focus:ring-blue-500 shadow-sm"
                                    placeholder="e.g. 45"
                                />
                                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-slate-400 dark:text-gray-500 font-medium">
                                    YRS
                                </span>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700 dark:text-gray-300">Gender</label>
                            <select
                                value={formData.Gender}
                                onChange={(e) => handleChange('Gender', e.target.value)}
                                className="w-full rounded-lg border-slate-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white py-2.5 focus:border-blue-500 focus:ring-blue-500 shadow-sm"
                            >
                                <option value="">Select Gender</option>
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700 dark:text-gray-300">Medical Unit / Ward</label>
                            <select
                                value={formData.Ward}
                                onChange={(e) => handleChange('Ward', e.target.value)}
                                className="w-full rounded-lg border-slate-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white py-2.5 focus:border-blue-500 focus:ring-blue-500 shadow-sm"
                            >
                                <option value="">Select Ward</option>
                                {wardOptions.map(w => (
                                    <option key={w.id || w.value} value={w.value}>{w.label}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>

                {/* Section B: Specimen & Culture */}
                <div className="p-6 space-y-4">
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-gray-400 flex items-center gap-2">
                        <Beaker className="w-4 h-4" />
                        Section B: Specimen & Culture Data (Day-0)
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700 dark:text-gray-300">Specimen Source <span className="text-red-500">*</span></label>
                            <select
                                value={formData.Sample_Type}
                                onChange={(e) => handleChange('Sample_Type', e.target.value)}
                                className="w-full rounded-lg border-slate-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white py-2.5 focus:border-blue-500 focus:ring-blue-500 shadow-sm"
                            >
                                <option value="">Select Specimen</option>
                                {sampleOptions.map(s => (
                                    <option key={s.id || s.value} value={s.value}>{s.label}</option>
                                ))}
                            </select>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700 dark:text-gray-300">Microscopy Cell Count <span className="text-red-500">*</span></label>
                            <select
                                value={formData.Cell_Count_Level}
                                onChange={(e) => handleChange('Cell_Count_Level', e.target.value)}
                                className="w-full rounded-lg border-slate-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white py-2.5 focus:border-blue-500 focus:ring-blue-500 shadow-sm"
                            >
                                <option value="">Select Level</option>
                                <option value="Low">Low (&lt;5 /hpf)</option>
                                <option value="Moderate">Moderate (5-25 /hpf)</option>
                                <option value="High">High (&gt;25 /hpf)</option>
                            </select>
                        </div>

                        {(formData.Sample_Type === 'Pus' || formData.Sample_Type === 'Wound') && (
                            <div className="space-y-2 animate-in fade-in slide-in-from-top-2">
                                <label className="text-sm font-medium text-slate-700 dark:text-gray-300">Pus/Wound Type</label>
                                <select
                                    value={formData.PUS_Type}
                                    onChange={(e) => handleChange('PUS_Type', e.target.value)}
                                    className="w-full rounded-lg border-slate-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white py-2.5 focus:border-blue-500 focus:ring-blue-500 shadow-sm"
                                >
                                    <option value="NA">Select Type</option>
                                    <option value="Abscess">Abscess</option>
                                    <option value="Wound_Pus">Wound Pus</option>
                                    <option value="ET_Secretion">ET Secretion</option>
                                </select>
                            </div>
                        )}

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700 dark:text-gray-300">Isolated Organism <span className="text-red-500">*</span></label>
                            <select
                                value={formData.Organism}
                                onChange={(e) => handleChange('Organism', e.target.value)}
                                className={`w-full rounded-lg py-2.5 shadow-sm transition-colors ${scopeError
                                    ? 'border-red-300 bg-red-50 dark:bg-red-500/10 dark:border-red-500/30 text-red-900 dark:text-red-400 focus:border-red-500 focus:ring-red-500'
                                    : 'border-slate-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:border-blue-500 focus:ring-blue-500'
                                    }`}
                            >
                                <option value="">Select Organism</option>

                                {/* In-scope Enterobacterales */}
                                <optgroup label="Module Scope (Enterobacterales)">
                                    <option value="E_coli">Escherichia coli</option>
                                    <option value="Klebsiella_pneumoniae">Klebsiella pneumoniae</option>
                                    <option value="Enterobacter_spp">Enterobacter spp.</option>
                                </optgroup>

                                {/* Out-of-scope examples for demo purposes */}
                                <optgroup label="Out of Scope">
                                    <option value="Pseudomonas_aeruginosa">Pseudomonas aeruginosa (Non-Fermenter)</option>
                                    <option value="Acinetobacter_baumannii">Acinetobacter baumannii (Non-Fermenter)</option>
                                    <option value="Staphylococcus_aureus">Staphylococcus aureus (MRSA)</option>
                                </optgroup>
                            </select>

                            {/* Scope Error Warning Banner */}
                            {scopeError && (
                                <div className="mt-2 text-sm text-red-600 flex items-start gap-1 animate-in zoom-in slide-in-from-top-1">
                                    <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                                    <span>{scopeError}</span>
                                </div>
                            )}
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-700 dark:text-gray-300">Culture Purity</label>
                            <select
                                value={formData.Pure_Growth}
                                onChange={(e) => handleChange('Pure_Growth', e.target.value)}
                                className="w-full rounded-lg border-slate-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white py-2.5 focus:border-blue-500 focus:ring-blue-500 shadow-sm bg-slate-50 dark:bg-gray-900"
                            >
                                <option value="Pure">Pure Growth (Standard)</option>
                                <option value="Mixed">Mixed Growth</option>
                            </select>
                            <p className="text-xs text-slate-400 dark:text-gray-500 mt-1 flex items-center gap-1">
                                Non-pure samples may reduce assessment certainty.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Footer / Actions */}
                <div className="p-6 bg-slate-50 dark:bg-gray-800/50 flex items-center justify-between rounded-b-xl border-t border-slate-200 dark:border-white/10">
                    <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-gray-400">
                        <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                        Clinical Stewardship System Ready
                    </div>

                    <button
                        type="submit"
                        disabled={loading || scopeError}
                        className={`flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium text-sm transition-all shadow-sm ${loading || scopeError
                            ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                            : 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-md active:scale-95'
                            }`}
                    >
                        {loading ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                Processing Clinical Profile...
                            </>
                        ) : (
                            <>
                                Generate Susceptibility Assessment
                                <ChevronRight className="w-4 h-4" />
                            </>
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
};

export default CaseRegistration;
