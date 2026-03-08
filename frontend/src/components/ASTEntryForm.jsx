import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    X, Save, AlertCircle, CheckCircle, Loader2,
    Trash2, FlaskConical, ChevronDown, Calendar,
    Hash, User, Building2, TestTube2
} from 'lucide-react';

const API = import.meta.env.VITE_API_URL;

// ── Design tokens ──────────────────────────────────────────────────────────
const glass = `bg-white/[0.03] border border-white/[0.07]`;

const inputCls = `w-full bg-white dark:bg-[#0b0f14] border border-slate-300 dark:border-white/[0.08] rounded-xl px-3.5 py-2.5
  text-[13px] text-slate-900 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-600
  focus:outline-none focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/10
  transition-all duration-200`;

const selectCls = `${inputCls} appearance-none cursor-pointer pr-8`;

// ── Field wrapper ──────────────────────────────────────────────────────────
const Field = ({ label, icon: Icon, children }) => (
    <div className="flex flex-col gap-1.5">
        <label className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-600 dark:text-slate-500">
            {Icon && <Icon className="w-3 h-3" />}
            {label}
        </label>
        {children}
    </div>
);

// ── Select with chevron ───────────────────────────────────────────────────
const Select = ({ name, value, onChange, children, highlight }) => (
    <div className="relative">
        <select name={name} value={value} onChange={onChange}
            className={`${selectCls} ${highlight ? 'text-violet-300 font-semibold border-violet-500/20' : ''}`}>
            {children}
        </select>
        <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500 dark:text-slate-600 pointer-events-none" />
    </div>
);

// ── SIR button ────────────────────────────────────────────────────────────
const SIRBtn = ({ opt, selected, onClick }) => {
    const cfg = {
        S: {
            active: 'bg-emerald-500 border-emerald-400 text-slate-900 dark:text-white shadow-emerald-500/30',
            idle: 'border-white/[0.07] text-slate-500 dark:text-slate-600 hover:border-emerald-500/40 hover:text-emerald-400 hover:bg-emerald-500/5',
            label: 'Susceptible',
        },
        I: {
            active: 'bg-amber-500 border-amber-400 text-slate-900 dark:text-white shadow-amber-500/30',
            idle: 'border-white/[0.07] text-slate-500 dark:text-slate-600 hover:border-amber-500/40 hover:text-amber-400 hover:bg-amber-500/5',
            label: 'Intermediate',
        },
        R: {
            active: 'bg-red-500 border-red-400 text-slate-900 dark:text-white shadow-red-500/30',
            idle: 'border-white/[0.07] text-slate-500 dark:text-slate-600 hover:border-red-500/40 hover:text-red-400 hover:bg-red-500/5',
            label: 'Resistant',
        },
    };
    return (
        <button
            type="button"
            title={cfg[opt].label}
            onClick={onClick}
            className={`relative w-9 h-9 rounded-lg font-black text-[11px] border
                        transition-all duration-150 active:scale-90
                        ${selected
                    ? `${cfg[opt].active} shadow-lg scale-105`
                    : `bg-slate-50 dark:bg-white/[0.03] border-slate-200 dark:${cfg[opt].idle}`}`}>
            {opt}
            {selected && (
                <motion.span
                    layoutId={`sir-glow-${opt}`}
                    className="absolute inset-0 rounded-lg opacity-20 blur-sm"
                    style={{ background: opt === 'S' ? '#10b981' : opt === 'I' ? '#f59e0b' : '#ef4444' }}
                />
            )}
        </button>
    );
};

// ── Skeleton row ──────────────────────────────────────────────────────────
const SkeletonRow = () => (
    <tr className="animate-pulse">
        <td className="px-5 py-[13px]">
            <div className="h-3.5 bg-white/[0.05] rounded-full w-44" />
        </td>
        <td className="px-5 py-[13px]">
            <div className="h-3.5 bg-white/[0.05] rounded-full w-28 mx-auto" />
        </td>
        <td />
    </tr>
);

// ── Main component ────────────────────────────────────────────────────────
const ASTEntryForm = ({ isOpen, onClose, onEntrySaved, defaultCultureDate }) => {
    const today = new Date().toISOString().split('T')[0];
    const effectiveDefault = defaultCultureDate || today;
    const minAllowedDate = effectiveDefault < today
        ? effectiveDefault
        : new Date(Date.now() - 21 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    const [metadata, setMetadata] = useState({
        ward: '', organism: '', specimen_type: '',
        lab_no: '', age: '', gender: 'Male', bht: '',
        culture_date: effectiveDefault,
    });
    const [panel, setPanel] = useState([]);
    const [panelLoading, setPanelLoading] = useState(false);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);
    const [wardOptions, setWardOptions] = useState([]);
    const [specimenOptions, setSpecimenOptions] = useState([]);
    const [organismOptions, setOrganismOptions] = useState([]);

    // Fetch master data on mount
    useEffect(() => {
        const load = async () => {
            try {
                const [wR, sR, oR] = await Promise.all([
                    fetch(`${API}/api/master/definitions/WARD`),
                    fetch(`${API}/api/master/definitions/SAMPLE_TYPE`),
                    fetch(`${API}/api/panels/organisms`),
                ]);
                if (wR.ok) {
                    const w = await wR.json(); setWardOptions(w);
                    if (w.length) setMetadata(p => ({ ...p, ward: w[0].value }));
                }
                if (sR.ok) {
                    const s = await sR.json(); setSpecimenOptions(s);
                    if (s.length) setMetadata(p => ({ ...p, specimen_type: s[0].value }));
                }
                if (oR.ok) {
                    const o = await oR.json(); setOrganismOptions(o);
                    if (o.length) setMetadata(p => ({ ...p, organism: o[0].name }));
                }
            } catch (e) { console.error('Master data load failed', e); }
        };
        load();
    }, []);

    // Fetch panel on organism change
    useEffect(() => {
        if (!metadata.organism) return;
        const ctrl = new AbortController();
        setPanelLoading(true);
        fetch(`${API}/api/panels/${encodeURIComponent(metadata.organism)}`, { signal: ctrl.signal })
            .then(r => r.json())
            .then(d => setPanel(d.map((x, i) => ({ id: i, antibiotic: x.display_name, result: '' }))))
            .catch(e => { if (e.name !== 'AbortError') console.error(e); })
            .finally(() => setPanelLoading(false));
        return () => ctrl.abort();
    }, [metadata.organism]);

    // Reset on open
    useEffect(() => {
        if (isOpen) {
            setMetadata(p => ({ ...p, culture_date: effectiveDefault }));
            setMessage(null);
        }
    }, [isOpen]);

    if (!isOpen) return null;

    const handleMeta = e => setMetadata(p => ({ ...p, [e.target.name]: e.target.value }));
    const handleResult = (id, res) => setPanel(p => p.map(r => r.id === id ? { ...r, result: res } : r));
    const removeDrug = id => setPanel(p => p.filter(r => r.id !== id));

    const completedCount = panel.filter(r => r.result !== '').length;

    const handleSubmit = async () => {
        setLoading(true); setMessage(null);
        const results = panel.filter(p => p.result).map(p => ({ antibiotic: p.antibiotic, result: p.result }));
        if (!results.length) {
            setMessage({ type: 'error', text: 'Please mark at least one antibiotic result.' });
            setLoading(false); return;
        }

        // Clean metadata (Pydantic wants null for optional ints, not empty strings)
        const cleanMetadata = { ...metadata };
        if (cleanMetadata.age === '') cleanMetadata.age = null;
        if (cleanMetadata.lab_no === '') cleanMetadata.lab_no = null;
        if (cleanMetadata.bht === '') cleanMetadata.bht = null;

        try {
            const res = await fetch(`${API}/api/entry`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...cleanMetadata, results }),
            });
            const data = await res.json();
            if (res.ok) {
                setMessage({ type: 'success', text: data.message || 'AST Result saved successfully' });
                setTimeout(() => { onClose(); onEntrySaved?.(); }, 1500);
            } else {
                let errorMsg = 'Submission failed.';
                if (Array.isArray(data.detail)) {
                    errorMsg = data.detail.map(e => `${e.loc.slice(1).join('.')}: ${e.msg}`).join(' | ');
                } else if (typeof data.detail === 'string') {
                    errorMsg = data.detail;
                }
                setMessage({ type: 'error', text: errorMsg });
            }
        } catch {
            setMessage({ type: 'error', text: 'Network error — please try again.' });
        } finally { setLoading(false); }
    };

    return (
        <AnimatePresence>
            {/* Backdrop */}
            <motion.div
                key="backdrop"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                onClick={onClose}
                className="fixed inset-0 z-50 flex items-center justify-center"
                style={{ background: 'rgba(0,0,0,0.80)', backdropFilter: 'blur(12px)' }}
            >
                {/* Modal */}
                <motion.div
                    key="modal"
                    initial={{ opacity: 0, scale: 0.96, y: 16 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.96, y: 16 }}
                    transition={{ duration: 0.22, ease: [0.25, 0.46, 0.45, 0.94] }}
                    onClick={e => e.stopPropagation()}
                    className="w-[860px] max-h-[92vh] flex flex-col rounded-2xl overflow-hidden
                               bg-[#080c11] border border-white/[0.08] shadow-2xl shadow-black/60"
                >
                    {/* ── Ambient glow ─────────────────────────────────── */}
                    <div className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2
                                    w-96 h-48 bg-indigo-600/10 rounded-full blur-3xl" />

                    {/* ── Header ───────────────────────────────────────── */}
                    <div className="relative flex items-center justify-between px-7 py-5
                                    border-b border-white/[0.06]">
                        <div className="flex items-center gap-3.5">
                            <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20
                                            flex items-center justify-center flex-shrink-0">
                                <FlaskConical className="w-4 h-4 text-indigo-400" />
                            </div>
                            <div>
                                <h2 className="text-[15px] font-semibold text-slate-900 dark:text-white tracking-tight">
                                    Clinical Isolate Entry
                                </h2>
                                <p className="text-[11px] text-slate-500 dark:text-slate-500 mt-0.5">
                                    Record susceptibility panel for a single patient isolate
                                </p>
                            </div>
                        </div>
                        <button onClick={onClose}
                            className="w-8 h-8 rounded-lg flex items-center justify-center
                                       text-slate-500 dark:text-slate-600 hover:text-slate-700 dark:text-slate-300 hover:bg-white/[0.06]
                                       border border-transparent hover:border-white/[0.08]
                                       transition-all duration-150">
                            <X className="w-4 h-4" />
                        </button>
                    </div>

                    {/* ── Scrollable body ───────────────────────────────── */}
                    <div className="flex-1 overflow-y-auto px-7 py-6 space-y-6
                                    scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">

                        {/* Predicted week banner */}
                        {effectiveDefault !== today && (
                            <motion.div
                                initial={{ opacity: 0, y: -6 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="flex items-start gap-3.5 px-4 py-3.5 rounded-xl
                                           bg-indigo-500/[0.06] border border-indigo-500/20">
                                <div className="w-7 h-7 rounded-lg bg-indigo-500/15 border border-indigo-500/25
                                                flex items-center justify-center flex-shrink-0 mt-0.5">
                                    <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                                </div>
                                <div>
                                    <p className="text-[12px] font-semibold text-indigo-300">
                                        Submitting for Predicted Week
                                    </p>
                                    <p className="text-[11px] text-slate-500 dark:text-slate-500 mt-0.5 leading-relaxed">
                                        Culture date pre-filled to{' '}
                                        <span className="text-indigo-300 font-medium">{effectiveDefault}</span>
                                        {' '}(AI-forecasted week start). Adjust below if the actual collection date differs.
                                    </p>
                                </div>
                            </motion.div>
                        )}

                        {/* ── Metadata grid ────────────────────────────── */}
                        <div className={`${glass} rounded-xl p-5`}>
                            <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-600 mb-4">
                                Isolate Information
                            </p>
                            <div className="grid grid-cols-3 gap-4">

                                <Field label="Ward" icon={Building2}>
                                    <Select name="ward" value={metadata.ward} onChange={handleMeta}>
                                        {wardOptions.map(w => <option key={w.id} value={w.value}>{w.label}</option>)}
                                        {!wardOptions.length && <option value="ICU">ICU</option>}
                                    </Select>
                                </Field>

                                <Field label="Specimen" icon={TestTube2}>
                                    <Select name="specimen_type" value={metadata.specimen_type} onChange={handleMeta}>
                                        {specimenOptions.map(s => <option key={s.id} value={s.value}>{s.label}</option>)}
                                        {!specimenOptions.length && <option value="Urine">Urine</option>}
                                    </Select>
                                </Field>

                                <Field label="Organism" icon={FlaskConical}>
                                    <Select name="organism" value={metadata.organism} onChange={handleMeta} highlight>
                                        {organismOptions.map(o => <option key={o.id} value={o.name}>{o.name}</option>)}
                                        {!organismOptions.length && <option value="">Loading…</option>}
                                    </Select>
                                </Field>

                                <Field label="Culture Date" icon={Calendar}>
                                    <input
                                        type="date"
                                        name="culture_date"
                                        value={metadata.culture_date}
                                        onChange={handleMeta}
                                        min={minAllowedDate}
                                        max={today}
                                        className={`${inputCls} [&::-webkit-calendar-picker-indicator]:invert-[0.5] cursor-pointer`}
                                    />
                                </Field>

                                <Field label="Lab Number" icon={Hash}>
                                    <input type="text" name="lab_no"
                                        placeholder="e.g. LAB-20241"
                                        onChange={handleMeta}
                                        className={inputCls} />
                                </Field>

                                <Field label="BHT Number" icon={Hash}>
                                    <input type="text" name="bht"
                                        placeholder="e.g. BHT-0042"
                                        onChange={handleMeta}
                                        className={inputCls} />
                                </Field>

                                {/* Age + Gender row */}
                                <div className="col-span-3 grid grid-cols-3 gap-4">
                                    <Field label="Patient Age" icon={User}>
                                        <input type="number" name="age"
                                            placeholder="Years"
                                            onChange={handleMeta}
                                            className={inputCls} />
                                    </Field>
                                    <Field label="Gender" icon={User}>
                                        <Select name="gender" value={metadata.gender} onChange={handleMeta}>
                                            <option>Male</option>
                                            <option>Female</option>
                                        </Select>
                                    </Field>
                                    {/* Spacer */}
                                    <div />
                                </div>
                            </div>
                        </div>

                        {/* ── Antibiogram table ─────────────────────────── */}
                        <div>
                            {/* Table header bar */}
                            <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-2.5">
                                    <p className="text-[13px] font-semibold text-slate-900 dark:text-white">
                                        Antibiogram
                                    </p>
                                    {panelLoading && (
                                        <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
                                    )}
                                    {!panelLoading && panel.length > 0 && (
                                        <span className="text-[11px] text-slate-500 dark:text-slate-600">
                                            {completedCount}/{panel.length} marked
                                        </span>
                                    )}
                                </div>
                                <span className="text-[10px] text-slate-700 uppercase tracking-widest">
                                    DB Panel · {metadata.organism || '—'}
                                </span>
                            </div>

                            {/* Progress bar */}
                            {!panelLoading && panel.length > 0 && (
                                <div className="h-0.5 bg-white/[0.05] rounded-full mb-4 overflow-hidden">
                                    <motion.div
                                        className="h-full bg-indigo-500/50 rounded-full"
                                        animate={{ width: `${(completedCount / panel.length) * 100}%` }}
                                        transition={{ duration: 0.3 }}
                                    />
                                </div>
                            )}

                            {/* Table */}
                            <div className="rounded-xl overflow-hidden border border-white/[0.06]">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-white/[0.05] bg-white/[0.02]">
                                            <th className="px-5 py-3 text-left text-[10px] font-bold uppercase
                                                           tracking-[0.12em] text-slate-500 dark:text-slate-600 w-1/2">
                                                Antibiotic
                                            </th>
                                            <th className="px-5 py-3 text-center text-[10px] font-bold uppercase
                                                           tracking-[0.12em] text-slate-500 dark:text-slate-600">
                                                S &nbsp;·&nbsp; I &nbsp;·&nbsp; R
                                            </th>
                                            <th className="w-12" />
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/[0.04]">

                                        {panelLoading
                                            ? [1, 2, 3, 4, 5, 6].map(i => <SkeletonRow key={i} />)
                                            : panel.map((row, idx) => (
                                                <motion.tr
                                                    key={row.id}
                                                    initial={{ opacity: 0, x: -6 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: idx * 0.03, duration: 0.18 }}
                                                    className={`group transition-colors duration-100
                                                        ${row.result
                                                            ? 'bg-white/[0.015]'
                                                            : 'hover:bg-white/[0.02]'}`}>

                                                    {/* Antibiotic name */}
                                                    <td className="px-5 py-3">
                                                        <div className="flex items-center gap-2.5">
                                                            {/* completion dot */}
                                                            <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 transition-colors duration-200
                                                                ${row.result === 'S' ? 'bg-emerald-500' :
                                                                    row.result === 'I' ? 'bg-amber-500' :
                                                                        row.result === 'R' ? 'bg-red-500' :
                                                                            'bg-white/[0.08]'}`} />
                                                            <span className="text-[13px] text-slate-700 dark:text-slate-300 font-medium">
                                                                {row.antibiotic}
                                                            </span>
                                                        </div>
                                                    </td>

                                                    {/* SIR buttons */}
                                                    <td className="px-5 py-3">
                                                        <div className="flex items-center justify-center gap-2">
                                                            {['S', 'I', 'R'].map(opt => (
                                                                <SIRBtn
                                                                    key={opt} opt={opt}
                                                                    selected={row.result === opt}
                                                                    onClick={() => handleResult(row.id, opt)}
                                                                />
                                                            ))}
                                                        </div>
                                                    </td>

                                                    {/* Remove */}
                                                    <td className="px-3 py-3 text-center">
                                                        <button onClick={() => removeDrug(row.id)}
                                                            className="opacity-0 group-hover:opacity-100
                                                                       text-slate-700 hover:text-red-400
                                                                       transition-all duration-150">
                                                            <Trash2 className="w-3.5 h-3.5" />
                                                        </button>
                                                    </td>
                                                </motion.tr>
                                            ))
                                        }

                                        {/* Empty state */}
                                        {!panelLoading && panel.length === 0 && (
                                            <tr>
                                                <td colSpan={3} className="px-5 py-14 text-center">
                                                    <FlaskConical className="w-7 h-7 text-slate-300 dark:text-slate-800 mx-auto mb-2" />
                                                    <p className="text-[13px] text-slate-500 dark:text-slate-600">
                                                        Select an organism to load its antibiotic panel
                                                    </p>
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* ── Footer ───────────────────────────────────────── */}
                    <div className="flex items-center justify-between px-7 py-4
                                    border-t border-white/[0.06] bg-white/[0.01]">

                        {/* Status message */}
                        <AnimatePresence mode="wait">
                            {message ? (
                                <motion.div
                                    key="msg"
                                    initial={{ opacity: 0, x: -8 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0 }}
                                    className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-[12px]
                                                font-medium border
                                                ${message.type === 'success'
                                            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                                            : 'bg-red-500/10 border-red-500/20 text-red-300'}`}>
                                    {message.type === 'success'
                                        ? <CheckCircle className="w-3.5 h-3.5" />
                                        : <AlertCircle className="w-3.5 h-3.5" />}
                                    {message.text}
                                </motion.div>
                            ) : (
                                <div key="hint" className="text-[11px] text-slate-700">
                                    {completedCount > 0
                                        ? `${completedCount} result${completedCount !== 1 ? 's' : ''} ready to submit`
                                        : 'Mark S / I / R for each antibiotic'}
                                </div>
                            )}
                        </AnimatePresence>

                        {/* Actions */}
                        <div className="flex items-center gap-3">
                            <button type="button" onClick={onClose}
                                className="px-4 py-2.5 text-[13px] text-slate-500 dark:text-slate-500 hover:text-slate-300 dark:text-slate-800 dark:text-slate-200
                                           transition-colors duration-150">
                                Cancel
                            </button>
                            <button
                                onClick={handleSubmit}
                                disabled={loading || completedCount === 0}
                                className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-[13px]
                                           font-semibold text-slate-900 dark:text-white bg-indigo-600 hover:bg-indigo-500
                                           shadow-lg shadow-indigo-600/20
                                           disabled:opacity-30 disabled:cursor-not-allowed
                                           transition-all duration-200 active:scale-95">
                                {loading ? (
                                    <><Loader2 className="w-4 h-4 animate-spin" /> Saving…</>
                                ) : (
                                    <><Save className="w-4 h-4" /> Commit Panel</>
                                )}
                            </button>
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
};

export default ASTEntryForm;
