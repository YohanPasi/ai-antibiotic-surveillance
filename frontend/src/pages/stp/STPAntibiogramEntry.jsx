import React, { useState } from 'react';
import { Plus, Trash2, Save, ShieldAlert, ClipboardList, CheckCircle } from 'lucide-react';

const API = 'http://localhost:8000';

const ANTIBIOTICS = [
    'Ceftriaxone', 'Ciprofloxacin', 'Meropenem', 'Amikacin',
    'Vancomycin', 'Linezolid', 'Gentamicin', 'Ampicillin',
    'Piperacillin-Tazobactam', 'Cefepime'
];
const WARDS = ['ICU', 'Surgical Ward A', 'Surgical Ward B', 'Surgical Ward C', 'Medical Ward A', 'Medical Ward B', 'Burn Unit'];
const ORGANISMS = [
    'Streptococcus pneumoniae', 'Streptococcus agalactiae', 'Viridans streptococci',
    'Enterococcus faecalis', 'Enterococcus faecium',
    'Escherichia coli', 'Klebsiella pneumoniae', 'Pseudomonas aeruginosa',
    'Staphylococcus aureus', 'Acinetobacter baumannii'
];

const AST_COLORS = {
    S: { active: 'bg-emerald-500 text-white border-emerald-500', label: 'S — Sensitive' },
    I: { active: 'bg-amber-500 text-white border-amber-500', label: 'I — Intermediate' },
    R: { active: 'bg-red-500 text-white border-red-500', label: 'R — Resistant' },
    NA: { active: 'bg-gray-500 text-white border-gray-500', label: 'Not Tested' },
};

const STPAntibiogramEntry = () => {
    const [form, setForm] = useState({ ward: '', organism: '', sample_date: '', data_source: 'MANUAL', isolates: [[]] });
    const [acknowledged, setAcknowledged] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [result, setResult] = useState(null); // {type: 'success'|'error', msg}

    const addIsolate = () => setForm(p => ({ ...p, isolates: [...p.isolates, []] }));
    const removeIsolate = (idx) => setForm(p => ({ ...p, isolates: p.isolates.filter((_, i) => i !== idx) }));

    const updateAST = (isolateIdx, antibiotic, value) => {
        const newIsolates = form.isolates.map((iso, i) => {
            if (i !== isolateIdx) return iso;
            const existing = iso.findIndex(a => a.antibiotic === antibiotic);
            if (existing >= 0) return iso.map((a, ai) => ai === existing ? { ...a, result: value } : a);
            return [...iso, { antibiotic, result: value }];
        });
        setForm(p => ({ ...p, isolates: newIsolates }));
    };

    const getAST = (isolate, antibiotic) => isolate.find(a => a.antibiotic === antibiotic)?.result;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setResult(null);
        try {
            const res = await fetch(`${API}/api/stp/feedback/antibiogram`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form)
            });
            const data = await res.json();
            if (res.ok) {
                setResult({ type: 'success', msg: `${data.inserted} record(s) saved successfully.${data.duplicates_rejected > 0 ? ` ${data.duplicates_rejected} duplicate(s) were skipped.` : ''}` });
                setForm({ ward: '', organism: '', sample_date: '', data_source: 'MANUAL', isolates: [[]] });
                setAcknowledged(false);
            } else {
                setResult({ type: 'error', msg: data.detail || 'Submission failed. Please try again.' });
            }
        } catch {
            setResult({ type: 'error', msg: 'Network error. Please check your connection.' });
        } finally {
            setSubmitting(false);
        }
    };

    const canSubmit = acknowledged && !submitting && form.ward && form.organism && form.sample_date;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Lab Results Entry</h1>
                <p className="text-sm text-slate-500 mt-0.5">Submit culture and sensitivity test results for surveillance tracking</p>
            </div>

            {/* Success / Error Banner */}
            {result && (
                <div className={`rounded-xl p-4 flex items-start gap-3 border ${result.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
                    {result.type === 'success' ? <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" /> : <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />}
                    <p className="text-sm font-medium">{result.msg}</p>
                </div>
            )}

            {/* Acknowledgment */}
            <div className={`rounded-xl border-2 p-4 transition-colors ${acknowledged ? 'bg-emerald-50 border-emerald-300' : 'bg-red-50 border-red-300'}`}>
                <label className="flex items-start gap-3 cursor-pointer">
                    <input
                        type="checkbox"
                        checked={acknowledged}
                        onChange={e => setAcknowledged(e.target.checked)}
                        className="mt-1 w-5 h-5 accent-emerald-600 cursor-pointer"
                    />
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <ShieldAlert className={`w-4 h-4 ${acknowledged ? 'text-emerald-600' : 'text-red-600'}`} />
                            <span className={`font-bold text-sm ${acknowledged ? 'text-emerald-900' : 'text-red-900'}`}>Acknowledgment Required</span>
                        </div>
                        <p className="text-sm text-slate-700 leading-relaxed">
                            I confirm that the results entered here are for <strong>surveillance and epidemiological monitoring only</strong>.
                            This data must <strong>not</strong> be used to guide individual patient treatment.
                        </p>
                    </div>
                </label>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Specimen Info */}
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <ClipboardList className="w-5 h-5 text-purple-600" />
                        <h2 className="font-semibold text-slate-800 dark:text-white">Specimen Information</h2>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {[
                            { label: 'Ward', key: 'ward', options: WARDS, placeholder: 'Select Ward' },
                            { label: 'Organism', key: 'organism', options: ORGANISMS, placeholder: 'Select Organism' },
                        ].map(({ label, key, options, placeholder }) => (
                            <div key={key}>
                                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">{label} *</label>
                                <select
                                    value={form[key]}
                                    onChange={e => setForm(p => ({ ...p, [key]: e.target.value }))}
                                    required
                                    className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-400"
                                >
                                    <option value="">{placeholder}</option>
                                    {options.map(o => <option key={o} value={o}>{o}</option>)}
                                </select>
                            </div>
                        ))}
                        <div>
                            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Sample Date *</label>
                            <input
                                type="date"
                                value={form.sample_date}
                                onChange={e => setForm(p => ({ ...p, sample_date: e.target.value }))}
                                max={new Date().toISOString().split('T')[0]}
                                required
                                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-400"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Entry Method</label>
                            <select
                                value={form.data_source}
                                onChange={e => setForm(p => ({ ...p, data_source: e.target.value }))}
                                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 text-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-400"
                            >
                                <option value="MANUAL">Manual Entry</option>
                                <option value="LIS">Lab System (LIS)</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* AST Results per Isolate */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="font-semibold text-slate-800 dark:text-white">Sensitivity Results</h2>
                            <p className="text-xs text-slate-500 mt-0.5">Select S (Sensitive), I (Intermediate), R (Resistant), or leave unselected if not tested</p>
                        </div>
                        <button
                            type="button"
                            onClick={addIsolate}
                            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors shadow-sm"
                        >
                            <Plus className="w-4 h-4" /> Add Isolate
                        </button>
                    </div>

                    {form.isolates.map((isolate, idx) => (
                        <div key={idx} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
                            <div className="flex items-center justify-between px-5 py-3 bg-gray-50 dark:bg-gray-700 border-b border-gray-100 dark:border-gray-600">
                                <h3 className="font-semibold text-sm text-slate-700 dark:text-gray-200">Isolate {idx + 1}</h3>
                                {idx > 0 && (
                                    <button type="button" onClick={() => removeIsolate(idx)}
                                        className="flex items-center gap-1 text-xs text-red-500 hover:text-red-700">
                                        <Trash2 className="w-3.5 h-3.5" /> Remove
                                    </button>
                                )}
                            </div>
                            <div className="p-5 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                                {ANTIBIOTICS.map(ab => {
                                    const selected = getAST(isolate, ab);
                                    return (
                                        <div key={ab}>
                                            <label className="block text-xs font-semibold text-slate-500 mb-2 truncate" title={ab}>{ab}</label>
                                            <div className="grid grid-cols-4 gap-0.5">
                                                {['S', 'I', 'R', 'NA'].map(r => (
                                                    <button
                                                        key={r}
                                                        type="button"
                                                        onClick={() => updateAST(idx, ab, r)}
                                                        className={`py-1.5 text-xs font-bold rounded border transition-all ${selected === r
                                                            ? AST_COLORS[r].active
                                                            : 'bg-white dark:bg-gray-700 border-gray-200 dark:border-gray-600 text-slate-500 hover:border-gray-400'
                                                            }`}
                                                    >
                                                        {r}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Legend */}
                <div className="flex items-center gap-4 text-xs text-slate-500 flex-wrap">
                    {Object.entries(AST_COLORS).map(([k, v]) => (
                        <span key={k} className="flex items-center gap-1.5">
                            <span className={`w-5 h-5 rounded flex items-center justify-center text-white text-xs font-bold ${v.active.split(' ')[0]}`}>{k}</span>
                            {v.label}
                        </span>
                    ))}
                </div>

                {/* Submit */}
                <button
                    type="submit"
                    disabled={!canSubmit}
                    className={`w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold text-sm transition-all duration-200 shadow-sm ${canSubmit ? 'bg-emerald-600 text-white hover:bg-emerald-700 shadow-emerald-200' : 'bg-gray-100 text-gray-400 cursor-not-allowed'}`}
                >
                    <Save className="w-4 h-4" />
                    {submitting ? 'Saving results…' : 'Save Lab Results'}
                </button>

                {!acknowledged && (
                    <p className="text-xs text-red-500 text-center">Please acknowledge the notice above before saving</p>
                )}
            </form>
        </div>
    );
};

export default STPAntibiogramEntry;
