import React, { useState, useEffect } from 'react';
import { PlusCircle } from 'lucide-react';
import MRSAResultPanel from './MRSAResultPanel';
import MRSAValidationLog from './MRSAValidationLog';
import ASTEntryForm from './ASTEntryForm';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const MRSAPage = () => {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [wardOptions, setWardOptions] = useState([]);
    const [sampleOptions, setSampleOptions] = useState([]);
    const [activeTab, setActiveTab] = useState('screening');
    const [isEntryOpen, setIsEntryOpen] = useState(false);

    const [formData, setFormData] = useState({
        ward: '',
        sample_type: 'Blood',
        gram_stain: 'GPC',
        cell_count_category: 'LOW',
        growth_time: null,
        recent_antibiotic_use: 'Unknown',
        length_of_stay: 1,
        // Record-keeping only — stripped before POST
        bht: '',
    });

    useEffect(() => {
        const fetchMasterData = async () => {
            try {
                const [wardRes, sampleRes] = await Promise.all([
                    fetch(`${API_URL}/api/master/definitions/WARD`),
                    fetch(`${API_URL}/api/master/definitions/SAMPLE_TYPE`),
                ]);
                if (wardRes.ok) {
                    const wards = await wardRes.json();
                    setWardOptions(wards);
                    if (wards.length > 0) setFormData(p => ({ ...p, ward: wards[0].value }));
                }
                if (sampleRes.ok) {
                    const samples = await sampleRes.json();
                    setSampleOptions(samples);
                }
            } catch (err) {
                console.error('Failed to load master data', err);
            }
        };
        fetchMasterData();
    }, []);

    const handleChange = e => {
        const { name, value } = e.target;

        // Immediate numeric conversion — prevents string/number type mismatch in payload
        if (name === 'length_of_stay') {
            const num = value === '' ? 0 : Number(value);
            if (num < 0) return;  // block negative typing at input
            setFormData(p => ({ ...p, length_of_stay: num }));
            return;
        }
        if (name === 'growth_time') {
            const num = value === '' ? null : Number(value);
            if (num !== null && num < 0) return;  // block negative typing at input
            setFormData(p => ({ ...p, growth_time: num }));
            return;
        }

        if (name === 'sample_type') {
            // When switching away from Blood: clear growth_time.
            // When switching TO Blood: leave null — user must enter manually.
            setFormData(p => ({
                ...p,
                sample_type: value,
                growth_time: value === 'Blood' ? p.growth_time : null,
            }));
        } else {
            setFormData(p => ({ ...p, [name]: value }));
        }
    };

    const handleSubmit = async e => {
        e.preventDefault();

        // Client-side validation
        if (Number(formData.length_of_stay) < 0) {
            setError('Days in hospital cannot be negative.');
            return;
        }
        if (formData.sample_type === 'Blood' && (formData.growth_time === null || Number(formData.growth_time) < 0)) {
            setError('Culture growth time is required for blood samples and must be ≥ 0.');
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);

        // Strip record-only fields — bht must not reach the model
        const { bht, ...modelPayload } = formData;
        // Numerics are already correct types from handleChange — no conversion needed here

        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_URL}/api/mrsa/predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(modelPayload),
            });
            if (!res.ok) {
                const e = await res.json();
                throw new Error(e.detail || 'Screening failed. Please try again.');
            }
            setResult(await res.json());
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const inputCls = "w-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors placeholder-slate-400 dark:placeholder-slate-500";
    const selectCls = "w-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 text-slate-900 dark:text-slate-100 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors appearance-none";
    const labelCls = "block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1";

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
            <div className="max-w-7xl mx-auto px-6 py-8">

                {/* Page header */}
                <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center flex-shrink-0">
                                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                                </svg>
                            </div>
                            <h1 className="text-xl font-semibold text-slate-900 dark:text-white">MRSA Risk Screening</h1>
                            <span className="ml-1 px-2 py-0.5 bg-blue-900 text-blue-300 text-xs rounded border border-blue-700">Before Culture Result</span>
                        </div>
                        <p className="text-slate-600 dark:text-slate-400 text-sm md:ml-11">
                            Early risk assessment for Staphylococcus aureus - fill in specimen and patient details to get a screening result.
                        </p>
                    </div>

                    <button
                        onClick={() => setIsEntryOpen(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 text-sm font-medium rounded-lg transition-colors shadow-lg"
                    >
                        <PlusCircle className="w-4 h-4 text-blue-400" />
                        Add Lab Result
                    </button>
                </div>

                {/* Main layout */}
                <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">

                    {/* Left: Form */}
                    <div className="xl:col-span-2 relative">
                        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden sticky top-8 shadow-xl shadow-black/20">
                            <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-white dark:from-slate-800 to-slate-50 dark:to-slate-800/80">
                                <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-200 flex items-center gap-2">
                                    <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                                    Specimen & Patient Details
                                </h2>
                                <p className="text-[11px] text-slate-500 dark:text-slate-500 mt-1 pl-6">All fields are used in the risk calculation</p>
                            </div>

                            <form onSubmit={handleSubmit} className="p-5 space-y-5">

                                {/* ── Section 1: Specimen Details ── */}
                                <div>
                                    <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-500 uppercase tracking-wider mb-2.5">Specimen Details</h3>
                                    <div className="grid grid-cols-2 gap-3">
                                        {/* Ward */}
                                        <div>
                                            <label className={labelCls}>Ward</label>
                                            <div className="relative">
                                                <select name="ward" value={formData.ward} onChange={handleChange} className={selectCls}>
                                                    {wardOptions.length === 0 && <option>Loading...</option>}
                                                    {wardOptions.map(o => <option key={o.id} value={o.value}>{o.label}</option>)}
                                                </select>
                                                <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 dark:text-slate-400">
                                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                                                </span>
                                            </div>
                                        </div>

                                        {/* Sample type */}
                                        <div>
                                            <label className={labelCls}>Sample type</label>
                                            <div className="relative">
                                                <select name="sample_type" value={formData.sample_type} onChange={handleChange} className={selectCls}>
                                                    {sampleOptions.length > 0
                                                        ? sampleOptions.map(o => <option key={o.id} value={o.value}>{o.label}</option>)
                                                        : (
                                                            <>
                                                                <option value="Blood">Blood</option>
                                                                <option value="Urine">Urine</option>
                                                                <option value="Wound">Wound</option>
                                                                <option value="Pus">Pus</option>
                                                                <option value="Swab">Swab</option>
                                                                <option value="Other">Other</option>
                                                            </>
                                                        )
                                                    }
                                                </select>
                                                <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 dark:text-slate-400">
                                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                                                </span>
                                            </div>
                                        </div>

                                        {/* Conditional growth time */}
                                        {formData.sample_type === 'Blood' && (
                                            <div className="col-span-2">
                                                <label className={labelCls}>Culture growth time (hrs)</label>
                                                <input
                                                    type="number"
                                                    name="growth_time"
                                                    value={formData.growth_time ?? ''}
                                                    onChange={handleChange}
                                                    className={inputCls}
                                                    step="0.5"
                                                    min={0}
                                                    placeholder="e.g. 18"
                                                    required={formData.sample_type === 'Blood'}
                                                />
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="border-t border-slate-200 dark:border-slate-700/60" />

                                {/* ── Section 2: Gram Stain & Microscopy ── */}
                                <div>
                                    <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-500 uppercase tracking-wider mb-2.5">Gram Stain & Microscopy</h3>
                                    <div className="grid grid-cols-2 gap-3">

                                        {/* Gram stain */}
                                        <div>
                                            <label className={labelCls}>Gram stain result</label>
                                            <div className="relative">
                                                <select name="gram_stain" value={formData.gram_stain} onChange={handleChange} className={selectCls}>
                                                    <option value="GPC">Gram-positive cocci</option>
                                                    <option value="Unknown">Not done / Unknown</option>
                                                </select>
                                                <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 dark:text-slate-400">
                                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                                                </span>
                                            </div>
                                        </div>

                                        {/* Pus cell count — categorical */}
                                        <div>
                                            <label className={labelCls}>Pus cell count</label>
                                            <div className="relative">
                                                <select name="cell_count_category" value={formData.cell_count_category} onChange={handleChange} className={selectCls}>
                                                    <option value="LOW">&lt;10 / HPF</option>
                                                    <option value="MEDIUM">10–25 / HPF</option>
                                                    <option value="HIGH">&gt;25 / HPF</option>
                                                </select>
                                                <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 dark:text-slate-400">
                                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                                                </span>
                                            </div>
                                            <p className="text-[10px] text-slate-500 dark:text-slate-500 mt-1">HPF = high-power field</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="border-t border-slate-200 dark:border-slate-700" />

                                {/* ── Section 3: Patient Risk Factors ── */}
                                <div>
                                    <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-500 uppercase tracking-wider mb-2.5">Patient Risk Factors</h3>
                                    <div className="grid grid-cols-2 gap-3">

                                        {/* Recent antibiotic use */}
                                        <div>
                                            <label className={labelCls}>Recent antibiotic use <span className="text-slate-600">(last 14 days)</span></label>
                                            <div className="relative">
                                                <select name="recent_antibiotic_use" value={formData.recent_antibiotic_use} onChange={handleChange} className={selectCls}>
                                                    <option value="Unknown">Unknown</option>
                                                    <option value="Yes">Yes</option>
                                                    <option value="No">No</option>
                                                </select>
                                                <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 dark:text-slate-400">
                                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                                                </span>
                                            </div>
                                        </div>

                                        {/* Length of stay */}
                                        <div>
                                            <label className={labelCls}>Days in hospital</label>
                                            <input
                                                type="number"
                                                name="length_of_stay"
                                                value={formData.length_of_stay}
                                                onChange={handleChange}
                                                className={inputCls}
                                                min={0}
                                                step={1}
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="border-t border-slate-200 dark:border-slate-700/60" />

                                {/* ── Section 4: Record Information ── */}
                                <div>
                                    <div className="flex justify-between items-center mb-1">
                                        <label className={labelCls} style={{ marginBottom: 0 }}>Patient BHT No.</label>
                                        <span className="text-[10px] text-slate-500 dark:text-slate-500">Optional / Record only</span>
                                    </div>
                                    <input
                                        type="text"
                                        name="bht"
                                        value={formData.bht}
                                        onChange={handleChange}
                                        className={inputCls}
                                        placeholder="e.g. BHT-2024-00142"
                                    />
                                </div>

                                {/* Error */}
                                {error && (
                                    <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 text-red-600 dark:text-red-300 text-sm">
                                        {error}
                                    </div>
                                )}

                                {/* Submit */}
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full py-3 rounded-lg font-semibold text-white text-sm bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 border border-blue-500/50 shadow-lg shadow-blue-900/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                                >
                                    {loading ? (
                                        <>
                                            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                            </svg>
                                            Analysing...
                                        </>
                                    ) : 'Get Screening Result'}
                                </button>

                                <p className="text-center text-[10px] text-slate-600">
                                    Screening aid only — not a replacement for clinical judgement
                                </p>
                            </form>
                        </div>
                    </div>

                    {/* Right: Tabs & Content */}
                    <div className="xl:col-span-3 flex flex-col h-[calc(100vh-140px)] min-h-[600px]">

                        {/* Tabs */}
                        <div className="flex gap-1 border-b border-slate-200 dark:border-slate-700 mb-5">
                            <button
                                onClick={() => setActiveTab('screening')}
                                className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${activeTab === 'screening' ? 'border-blue-500 text-blue-400' : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:text-slate-300'}`}
                            >
                                Current Screening
                            </button>
                            <button
                                onClick={() => setActiveTab('history')}
                                className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${activeTab === 'history' ? 'border-teal-500 text-teal-400' : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:text-slate-300'}`}
                            >
                                Validation History
                            </button>
                        </div>

                        {/* Content Area */}
                        <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                            {activeTab === 'screening' ? (
                                <MRSAResultPanel prediction={result} loading={loading} />
                            ) : (
                                <MRSAValidationLog />
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* AST Entry Modal Overlay */}
            <ASTEntryForm
                isOpen={isEntryOpen}
                onClose={() => setIsEntryOpen(false)}
                onEntrySaved={() => {
                    // Refetch logs or just close silently
                    setIsEntryOpen(false);
                    // Note: If MRSAValidationLog is active, we could trigger a refresh, 
                    // but since they have to wait for pipeline processing it's better to let them refresh manually via the built-in button.
                }}
            />

            <style>{`
                .custom-scrollbar::-webkit-scrollbar { width: 6px; }
                .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
                .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
            `}</style>
        </div>
    );
};

export default MRSAPage;
