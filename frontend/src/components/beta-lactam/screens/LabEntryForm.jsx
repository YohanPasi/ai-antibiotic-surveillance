import React, { useState } from 'react';
import { Beaker, ScanBarcode, ArrowRight, Save, ShieldCheck, FileCheck, CheckCircle2 } from 'lucide-react';
import { betaLactamService } from '../../../services/betaLactamService';

const LabEntryForm = ({ encounterId, inputContext, resultContext, onComplete, onSubmit }) => {
    // We group entry by generation. 
    // This perfectly aligns with our Beta-Lactam CDSS logic
    const astPanelMaster = {
        'Gen1': ['Cefalexin', 'Cefazolin'],
        'Gen2': ['Cefuroxime'],
        'Gen3': ['Ceftriaxone', 'Cefotaxime', 'Ceftazidime'],
        'Gen4': ['Cefepime'],
        'BL_Combo': ['Amoxiclav', 'Pip-Tazo'],
        'Carbapenem': ['Meropenem', 'Imipenem', 'Ertapenem']
    };

    const [astResults, setAstResults] = useState({});
    const [scannedId, setScannedId] = useState(encounterId || '');
    const [isSaving, setIsSaving] = useState(false);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [fetchedContext, setFetchedContext] = useState(null);
    const [searchError, setSearchError] = useState(null);

    const activeContext = inputContext || fetchedContext;

    const handleSearch = async (e) => {
        if (e) e.preventDefault();
        setSearchError(null);
        try {
            const record = await betaLactamService.getEncounter(scannedId);
            if (record && record.inputs) {
                setFetchedContext(record.inputs);
            } else {
                setFetchedContext(null);
                setSearchError("Encounter ID not found.");
            }
        } catch (err) {
            setSearchError("Error retrieving case.");
        }
    };

    const handleResultSelect = (antibiotic, value) => {
        setAstResults(prev => ({ ...prev, [antibiotic]: value }));
    };

    const handleSave = async () => {
        // Require at least one result
        if (Object.keys(astResults).length === 0) {
            alert("No AST results entered. Please select at least one Susceptibility result.");
            return;
        }

        setIsSaving(true);
        try {
            await betaLactamService.persistASTResults(scannedId, astResults, activeContext);
            setSaveSuccess(true);

            setTimeout(() => {
                const completionCallback = onComplete || onSubmit;
                if (completionCallback) {
                    completionCallback(scannedId, astResults, activeContext);
                }
            }, 1000);

        } catch (error) {
            console.error(error);
            alert("Failed to save AST results to the Database.");
            setIsSaving(false);
        }
    };

    // Calculate completion percentage
    const totalDrugs = Object.values(astPanelMaster).flat().length;
    const filledDrugs = Object.keys(astResults).length;
    const progress = Math.round((filledDrugs / totalDrugs) * 100);

    return (
        <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in zoom-in-95 duration-500">
            {/* Header */}
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-slate-200 dark:border-white/10 p-6 flex items-start gap-4">
                <div className="p-3 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-lg shrink-0">
                    <Beaker className="w-6 h-6" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Confirmatory AST Entry</h2>
                    <p className="text-slate-500 dark:text-gray-400 mt-1">
                        Enter the confirmed Antimicrobial Susceptibility Testing panel.
                        Results will be compared against the initial susceptibility assessments.
                    </p>
                </div>
            </div>

            {/* Encounter Setup */}
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-slate-200 dark:border-white/10 overflow-hidden text-sm">
                <div className="p-4 bg-slate-50 dark:bg-gray-800/50 border-b border-slate-100 dark:border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <ScanBarcode className="w-5 h-5 text-slate-400 dark:text-gray-500" />
                        <span className="font-bold text-slate-700 dark:text-gray-300">Scan / Link Encounter</span>
                    </div>
                </div>
                <div className="p-5 flex flex-col md:flex-row gap-6 items-start md:items-center">
                    <form onSubmit={handleSearch} className="flex-1 w-full relative flex gap-2">
                        <div className="relative flex-1">
                            <input
                                type="text"
                                value={scannedId}
                                onChange={(e) => setScannedId(e.target.value)}
                                className="w-full font-mono text-lg rounded-lg border-slate-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white py-3 px-4 focus:ring-indigo-500 focus:border-indigo-500 shadow-sm uppercase placeholder:text-slate-400 dark:placeholder:text-gray-600"
                                placeholder="Scan LAB-ID Barcode"
                                disabled={!!inputContext}
                            />
                            {activeContext && (
                                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                                    <span className="bg-emerald-100 dark:bg-emerald-900/40 text-emerald-800 dark:text-emerald-300 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                                        Linked
                                    </span>
                                </div>
                            )}
                        </div>
                        {!inputContext && (
                            <button type="submit" className="bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-4 rounded-lg font-bold hover:bg-slate-800 dark:hover:bg-slate-200 transition-colors">
                                Search
                            </button>
                        )}
                    </form>
                    {searchError && (
                        <div className="text-red-500 dark:text-red-400 text-sm font-bold flex-1">{searchError}</div>
                    )}
                    {activeContext && (
                        <div className="flex-1 grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                            <div className="text-slate-500 dark:text-gray-400">Organism: <span className="font-bold text-slate-800 dark:text-white">{activeContext.Organism?.replace('_', ' ')}</span></div>
                            <div className="text-slate-500 dark:text-gray-400">Age/Gender: <span className="font-bold text-slate-800 dark:text-white">{activeContext.Age} {activeContext.Gender}</span></div>
                            <div className="text-slate-500 dark:text-gray-400">Sample: <span className="font-bold text-slate-800 dark:text-white">{activeContext.Sample_Type}</span></div>
                            <div className="text-slate-500 dark:text-gray-400">Ward: <span className="font-bold text-slate-800 dark:text-white">{activeContext.Ward}</span></div>
                        </div>
                    )}
                </div>
            </div>

            {/* Lab Data Grid */}
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-slate-200 dark:border-white/10">
                <div className="p-5 border-b border-slate-100 dark:border-white/5 flex items-center justify-between bg-slate-50/50 dark:bg-gray-800/50">
                    <div>
                        <h3 className="font-bold text-slate-800 dark:text-white flex items-center gap-2">
                            <FileCheck className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                            Beta-Lactam Susceptibility Grid
                        </h3>
                    </div>
                    <div className="text-xs font-bold text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-100 dark:border-indigo-500/20 flex items-center gap-2">
                        {progress}% Complete
                    </div>
                </div>

                <div className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {Object.entries(astPanelMaster).map(([gen, drugs]) => (
                            <div key={gen} className="border border-slate-200 dark:border-white/10 rounded-lg overflow-hidden flex flex-col">
                                <div className="bg-slate-100 dark:bg-gray-800 px-3 py-2 border-b border-slate-200 dark:border-white/5 font-bold text-xs text-slate-700 dark:text-gray-300 uppercase tracking-wider flex items-center justify-between">
                                    {gen === 'BL_Combo' ? 'BL/BLI Combo' : gen}
                                    {resultContext && resultContext.spectrum[gen] && (
                                        <span className="text-[10px] bg-slate-200 dark:bg-gray-700 text-slate-600 dark:text-gray-300 px-1.5 py-0.5 rounded">
                                            Estimated: {resultContext.spectrum[gen].traffic_light}
                                        </span>
                                    )}
                                </div>
                                <div className="p-2 flex-grow bg-slate-50/30 dark:bg-gray-900 flex flex-col justify-end divide-y divide-slate-100 dark:divide-white/5">
                                    {drugs.map(drug => (
                                        <div key={drug} className="flex items-center justify-between py-2 px-1">
                                            <span className="text-sm font-medium text-slate-700 dark:text-gray-300">{drug}</span>
                                            <div className="flex gap-1.5">
                                                {['S', 'I', 'R'].map(val => (
                                                    <button
                                                        key={val}
                                                        type="button"
                                                        onClick={() => handleResultSelect(drug, val)}
                                                        className={`w-8 h-8 rounded-md font-bold text-xs flex items-center justify-center transition-all ${astResults[drug] === val
                                                            ? val === 'S' ? 'bg-green-500 text-white shadow-sm ring-2 ring-green-200 dark:ring-green-900 ring-offset-1 dark:ring-offset-gray-900'
                                                                : val === 'I' ? 'bg-amber-500 text-white shadow-sm ring-2 ring-amber-200 dark:ring-amber-900 ring-offset-1 dark:ring-offset-gray-900'
                                                                    : 'bg-red-500 text-white shadow-sm ring-2 ring-red-200 dark:ring-red-900 ring-offset-1 dark:ring-offset-gray-900'
                                                            : 'bg-white dark:bg-gray-800 border border-slate-200 dark:border-gray-700 text-slate-400 dark:text-gray-500 hover:border-slate-300 dark:hover:border-gray-600 hover:bg-slate-50 dark:hover:bg-gray-700'
                                                            }`}
                                                    >
                                                        {val}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="p-5 bg-slate-50 dark:bg-gray-800/50 border-t border-slate-200 dark:border-white/10 flex items-center justify-between rounded-b-xl">
                    <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-gray-400">
                        <ShieldCheck className="w-4 h-4 text-emerald-500" />
                        Results lock Empiric CDSS for this encounter.
                    </div>

                    <button
                        onClick={handleSave}
                        disabled={isSaving || filledDrugs === 0 || saveSuccess}
                        className={`flex items-center gap-2 px-8 py-3 rounded-lg font-bold text-sm transition-all shadow-sm ${isSaving
                            ? 'bg-indigo-400 text-white cursor-not-allowed'
                            : saveSuccess
                                ? 'bg-emerald-500 text-white shadow-md'
                                : filledDrugs > 0
                                    ? 'bg-indigo-600 text-white hover:bg-indigo-700 hover:shadow-md active:scale-95'
                                    : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                            }`}
                    >
                        {isSaving ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                Saving Matrix...
                            </>
                        ) : saveSuccess ? (
                            <>
                                <CheckCircle2 className="w-4 h-4" />
                                Saved to LIS
                            </>
                        ) : (
                            <>
                                <Save className="w-4 h-4" />
                                Submit Lab Validation
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LabEntryForm;
