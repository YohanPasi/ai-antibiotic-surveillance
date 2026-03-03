import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Plus, Trash2, Database, ChevronDown, FlaskConical,
    AlertCircle, Check, X, Building2, TestTube, ShieldCheck, Search
} from 'lucide-react';

const API = import.meta.env.VITE_API_URL;

// ── Design tokens ────────────────────────────────────────────────────────────
const glass = `bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl`;

const inputCls = `w-full bg-[#0c1015]/80 border border-white/[0.09] rounded-xl px-4 py-2.5
  text-sm text-slate-200 placeholder-slate-600
  focus:outline-none focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/10
  transition-all duration-200`;

const TAB_META = {
    WARD: { label: 'Hospital Wards', icon: Building2, accent: 'sky', dot: 'bg-sky-400' },
    SAMPLE_TYPE: { label: 'Sample Types', icon: TestTube, accent: 'violet', dot: 'bg-violet-400' },
    PANEL_CONFIG: { label: 'Antibiotic Panels', icon: ShieldCheck, accent: 'emerald', dot: 'bg-emerald-400' },
};

const ACCENT = {
    sky: { ring: 'ring-sky-500/30 border-sky-500/40', tag: 'bg-sky-500/10 border-sky-500/20 text-sky-300', btn: 'bg-sky-500 hover:bg-sky-400 shadow-sky-500/20' },
    violet: { ring: 'ring-violet-500/30 border-violet-500/40', tag: 'bg-violet-500/10 border-violet-500/20 text-violet-300', btn: 'bg-violet-500 hover:bg-violet-400 shadow-violet-500/20' },
    emerald: { ring: 'ring-emerald-500/30 border-emerald-500/40', tag: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300', btn: 'bg-emerald-500 hover:bg-emerald-400 shadow-emerald-500/20' },
};

// ── Micro components ─────────────────────────────────────────────────────────
const Pill = ({ label, accent, onRemove }) => (
    <motion.span
        layout
        initial={{ opacity: 0, scale: 0.88 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.88 }}
        transition={{ duration: 0.15 }}
        className={`inline-flex items-center gap-1.5 pl-3 pr-2 py-1 rounded-full
                    border text-[12px] font-medium select-none ${ACCENT[accent].tag}`}>
        {label}
        {onRemove && (
            <button
                onClick={onRemove}
                className="w-4 h-4 flex items-center justify-center rounded-full
                           hover:bg-white/10 transition-colors duration-100">
                <X className="w-2.5 h-2.5" />
            </button>
        )}
    </motion.span>
);

const PrimaryBtn = ({ children, accent = 'sky', onClick, disabled, type = 'button', className = '' }) => (
    <button
        type={type}
        onClick={onClick}
        disabled={disabled}
        className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-[13px] font-semibold
                    text-white shadow-lg transition-all duration-200 active:scale-95
                    disabled:opacity-30 disabled:cursor-not-allowed disabled:active:scale-100
                    ${ACCENT[accent].btn} shadow-${ACCENT[accent].btn.split(' ')[0].replace('bg-', '').replace('/', '-')}
                    ${className}`}>
        {children}
    </button>
);

const GhostBtn = ({ children, onClick, className = '' }) => (
    <button
        onClick={onClick}
        className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-[12px]
                    font-medium text-slate-500 hover:text-red-400 hover:bg-red-400/10
                    transition-all duration-200 ${className}`}>
        {children}
    </button>
);

const FieldLabel = ({ children }) => (
    <label className="block text-[11px] font-bold uppercase tracking-[0.1em] text-slate-500 mb-2">
        {children}
    </label>
);

const Divider = () => <div className="border-t border-white/[0.06] my-8" />;

const SkeletonRow = () => (
    <div className="flex items-center gap-3 px-4 py-3">
        <div className="w-2 h-2 rounded-full bg-white/5" />
        <div className="h-3.5 bg-white/5 rounded-full w-40 animate-pulse" />
    </div>
);

// ── Main component ────────────────────────────────────────────────────────────
const MasterDataManager = () => {
    const [tab, setTab] = useState('WARD');
    const [error, setError] = useState(null);

    // WARD / SAMPLE_TYPE
    const [items, setItems] = useState([]);
    const [loadingItems, setLoadingItems] = useState(false);
    const [newItem, setNewItem] = useState('');
    const [filter, setFilter] = useState('');

    // PANEL_CONFIG
    const [organisms, setOrganisms] = useState([]);
    const [selectedOrg, setSelectedOrg] = useState(null);
    const [currentPanel, setCurrentPanel] = useState([]);
    const [allAntibiotics, setAllAntibiotics] = useState([]);
    const [selectedAbxId, setSelectedAbxId] = useState('');
    const [panelLoading, setPanelLoading] = useState(false);
    const [newOrgName, setNewOrgName] = useState('');
    const [newAbxName, setNewAbxName] = useState('');
    const [newAbxCode, setNewAbxCode] = useState('');

    const token = () => localStorage.getItem('token');
    const authHdr = () => ({ 'Content-Type': 'application/json', Authorization: `Bearer ${token()}` });
    const accentKey = TAB_META[tab].accent;

    // ── Items (WARD / SAMPLE_TYPE) ───────────────────────────────────────────
    const fetchItems = useCallback(async () => {
        if (tab === 'PANEL_CONFIG') return;
        setLoadingItems(true); setError(null);
        try {
            const r = await fetch(`${API}/api/master/definitions/${tab}`);
            if (!r.ok) throw new Error('Failed to load');
            setItems(await r.json());
        } catch (e) { setError(e.message); }
        finally { setLoadingItems(false); }
    }, [tab]);

    useEffect(() => { fetchItems(); setFilter(''); }, [fetchItems]);

    const handleAddItem = async (e) => {
        e.preventDefault();
        if (!newItem.trim()) return;
        try {
            await fetch(`${API}/api/master/definitions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category: tab, label: newItem.trim(), value: newItem.trim() }),
            });
            setNewItem(''); fetchItems();
        } catch (e) { setError(e.message); }
    };

    const handleDeleteItem = async (id) => {
        await fetch(`${API}/api/master/definitions/${id}`, { method: 'DELETE' });
        fetchItems();
    };

    // ── Panel config ────────────────────────────────────────────────────────
    const fetchOrganisms = async () => {
        const r = await fetch(`${API}/api/panels/organisms`);
        const orgs = await r.json();
        setOrganisms(orgs);
        if (orgs.length && !selectedOrg) setSelectedOrg(orgs[0]);
    };

    const fetchAllAntibs = async () => {
        const r = await fetch(`${API}/api/panels/antibiotics`);
        setAllAntibiotics(await r.json());
    };

    const fetchPanel = async (org) => {
        if (!org) return;
        setPanelLoading(true);
        try {
            const r = await fetch(`${API}/api/panels/${encodeURIComponent(org.name)}`);
            setCurrentPanel(await r.json());
        } finally { setPanelLoading(false); }
    };

    useEffect(() => {
        if (tab === 'PANEL_CONFIG') { fetchOrganisms(); fetchAllAntibs(); }
    }, [tab]);

    useEffect(() => { if (selectedOrg) fetchPanel(selectedOrg); }, [selectedOrg]);

    const handleRemoveAbx = async (abxId) => {
        await fetch(`${API}/api/panels/mapping/${selectedOrg.id}/${abxId}`, { method: 'DELETE', headers: authHdr() });
        fetchPanel(selectedOrg);
    };

    const handleAddAbx = async () => {
        if (!selectedOrg || !selectedAbxId) return;
        await fetch(`${API}/api/panels/mapping`, {
            method: 'POST', headers: authHdr(),
            body: JSON.stringify({ organism_id: selectedOrg.id, antibiotic_id: parseInt(selectedAbxId) }),
        });
        setSelectedAbxId(''); fetchPanel(selectedOrg); fetchAllAntibs();
    };

    const handleCreateOrg = async (e) => {
        e.preventDefault();
        if (!newOrgName.trim()) return;
        const r = await fetch(`${API}/api/panels/organisms`, {
            method: 'POST', headers: authHdr(),
            body: JSON.stringify({ name: newOrgName.trim(), group_name: 'General' }),
        });
        if (!r.ok) { const d = await r.json(); setError(d.detail); return; }
        setNewOrgName(''); fetchOrganisms();
    };

    const handleCreateAbx = async (e) => {
        e.preventDefault();
        if (!newAbxName.trim()) return;
        const r = await fetch(`${API}/api/panels/antibiotics`, {
            method: 'POST', headers: authHdr(),
            body: JSON.stringify({ name: newAbxName.trim(), short_code: newAbxCode.trim() || null }),
        });
        if (!r.ok) { const d = await r.json(); setError(d.detail); return; }
        setNewAbxName(''); setNewAbxCode(''); fetchAllAntibs();
    };

    const panelIds = new Set(currentPanel.map(a => a.id));
    const availableToAdd = allAntibiotics.filter(a => !panelIds.has(a.id));
    const filteredItems = items.filter(i => i.label.toLowerCase().includes(filter.toLowerCase()));

    return (
        <div className="min-h-screen bg-[#060a0f] text-slate-200 relative overflow-hidden">
            {/* Ambient background glow */}
            <div className="pointer-events-none absolute inset-0 overflow-hidden">
                <div className={`absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full blur-[120px] opacity-[0.06]
                    ${accentKey === 'sky' ? 'bg-sky-400' : accentKey === 'violet' ? 'bg-violet-400' : 'bg-emerald-400'}`} />
            </div>

            <div className="relative z-10 max-w-4xl mx-auto px-8 py-12">

                {/* ── Page header ───────────────────────────────────────── */}
                <div className="mb-10">
                    <p className="text-[10px] font-bold tracking-[0.18em] uppercase text-slate-600 mb-2">Administration</p>
                    <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Master Data</h1>
                    <p className="text-sm text-slate-500">
                        Configure reference data and antibiotic surveillance panels
                    </p>
                </div>

                {/* ── Error ─────────────────────────────────────────────── */}
                <AnimatePresence>
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, y: -8 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -8 }}
                            className="mb-5 flex items-center gap-3 px-4 py-3 rounded-xl
                                       bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            <span className="flex-1">{error}</span>
                            <button onClick={() => setError(null)}
                                className="hover:text-red-300 transition-colors"><X className="w-4 h-4" /></button>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* ── Tab bar ───────────────────────────────────────────── */}
                <div className="flex gap-2 mb-8">
                    {Object.entries(TAB_META).map(([key, meta]) => {
                        const Icon = meta.icon;
                        const active = tab === key;
                        return (
                            <button
                                key={key}
                                onClick={() => { setTab(key); setError(null); }}
                                className={`relative flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm
                                            font-semibold transition-all duration-200
                                            ${active
                                        ? `${glass} text-white shadow-lg`
                                        : 'text-slate-500 hover:text-slate-300 hover:bg-white/[0.04]'}`}>
                                <Icon className="w-3.5 h-3.5" />
                                {meta.label}
                                {active && (
                                    <motion.span
                                        layoutId="tab-indicator"
                                        className={`absolute bottom-1.5 left-1/2 -translate-x-1/2 w-5 h-0.5 rounded-full ${meta.dot}`}
                                    />
                                )}
                            </button>
                        );
                    })}
                </div>

                {/* ── Content card ──────────────────────────────────────── */}
                <AnimatePresence mode="wait">
                    <motion.div
                        key={tab}
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        transition={{ duration: 0.2 }}
                        className={`${glass} rounded-2xl p-8`}>

                        {/* ── WARD / SAMPLE_TYPE ─────────────────────────── */}
                        {tab !== 'PANEL_CONFIG' && (
                            <>
                                {/* Add row */}
                                <form onSubmit={handleAddItem} className="flex gap-3 mb-8">
                                    <input
                                        type="text"
                                        value={newItem}
                                        onChange={e => setNewItem(e.target.value)}
                                        placeholder={tab === 'WARD' ? 'Add a ward (e.g. Cardiology ICU)' : 'Add a sample type (e.g. CSF)'}
                                        className={`${inputCls} flex-1`}
                                    />
                                    <PrimaryBtn
                                        type="submit"
                                        accent={accentKey}
                                        disabled={!newItem.trim()}>
                                        <Plus className="w-4 h-4" /> Add
                                    </PrimaryBtn>
                                </form>

                                {/* Search */}
                                {items.length > 6 && (
                                    <div className="relative mb-5">
                                        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600" />
                                        <input
                                            type="text"
                                            value={filter}
                                            onChange={e => setFilter(e.target.value)}
                                            placeholder="Search…"
                                            className={`${inputCls} pl-10`}
                                        />
                                    </div>
                                )}

                                {/* List */}
                                {loadingItems ? (
                                    <div className="space-y-1">
                                        {[1, 2, 3, 4].map(i => <SkeletonRow key={i} />)}
                                    </div>
                                ) : filteredItems.length === 0 ? (
                                    <div className="text-center py-16 text-slate-600">
                                        <Database className="w-8 h-8 mx-auto mb-3 opacity-30" />
                                        <p className="text-sm">{items.length === 0 ? 'No entries yet.' : 'No matches found.'}</p>
                                    </div>
                                ) : (
                                    <div className="space-y-1">
                                        <AnimatePresence>
                                            {filteredItems.map(item => (
                                                <motion.div
                                                    key={item.id}
                                                    layout
                                                    initial={{ opacity: 0, x: -8 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    exit={{ opacity: 0, x: -8 }}
                                                    className="group flex items-center justify-between px-4 py-3 rounded-xl
                                                               hover:bg-white/[0.04] transition-all duration-150">
                                                    <div className="flex items-center gap-3">
                                                        <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${TAB_META[tab].dot}`} />
                                                        <span className="text-sm text-slate-300">{item.label}</span>
                                                    </div>
                                                    <motion.div
                                                        initial={{ opacity: 0 }}
                                                        whileHover={{ opacity: 1 }}
                                                        className="opacity-0 group-hover:opacity-100 transition-opacity">
                                                        <GhostBtn onClick={() => handleDeleteItem(item.id)}>
                                                            <Trash2 className="w-3.5 h-3.5" /> Remove
                                                        </GhostBtn>
                                                    </motion.div>
                                                </motion.div>
                                            ))}
                                        </AnimatePresence>
                                    </div>
                                )}

                                {/* Count */}
                                {items.length > 0 && (
                                    <p className="text-[11px] text-slate-700 mt-5">
                                        {filteredItems.length} of {items.length} entries
                                    </p>
                                )}
                            </>
                        )}

                        {/* ── PANEL CONFIG ────────────────────────────────── */}
                        {tab === 'PANEL_CONFIG' && (
                            <div className="space-y-8">

                                {/* Organism selector */}
                                <div>
                                    <FieldLabel>Organism</FieldLabel>
                                    <div className="relative w-80">
                                        <select
                                            value={selectedOrg?.id || ''}
                                            onChange={e => setSelectedOrg(organisms.find(o => o.id === parseInt(e.target.value)))}
                                            className={`${inputCls} appearance-none pr-8 font-semibold text-emerald-300`}>
                                            {organisms.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}
                                        </select>
                                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600 pointer-events-none" />
                                    </div>
                                </div>

                                {/* Active panel */}
                                <div>
                                    <div className="flex items-baseline gap-3 mb-4">
                                        <FieldLabel>Active Panel</FieldLabel>
                                        {!panelLoading && (
                                            <span className="text-[11px] text-slate-600 -mt-2">
                                                {currentPanel.length} antibiotic{currentPanel.length !== 1 ? 's' : ''}
                                            </span>
                                        )}
                                    </div>

                                    {panelLoading ? (
                                        <div className="flex flex-wrap gap-2">
                                            {[1, 2, 3, 4, 5].map(i => (
                                                <div key={i} className="h-7 bg-white/[0.04] rounded-full animate-pulse w-28" />
                                            ))}
                                        </div>
                                    ) : currentPanel.length === 0 ? (
                                        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-white/[0.02] border border-white/[0.06] text-slate-600 text-sm">
                                            <FlaskConical className="w-4 h-4" />
                                            No antibiotics assigned to this panel yet.
                                        </div>
                                    ) : (
                                        <motion.div layout className="flex flex-wrap gap-2">
                                            <AnimatePresence>
                                                {currentPanel.map(abx => (
                                                    <Pill
                                                        key={abx.id}
                                                        label={abx.display_name}
                                                        accent="emerald"
                                                        onRemove={() => handleRemoveAbx(abx.id)}
                                                    />
                                                ))}
                                            </AnimatePresence>
                                        </motion.div>
                                    )}

                                    {/* Add antibiotic */}
                                    <div className="flex gap-3 mt-5">
                                        <div className="relative flex-1 max-w-sm">
                                            <select
                                                value={selectedAbxId}
                                                onChange={e => setSelectedAbxId(e.target.value)}
                                                className={`${inputCls} appearance-none pr-8`}>
                                                <option value="">Select antibiotic to add…</option>
                                                {availableToAdd.map(a => <option key={a.id} value={a.id}>{a.display_name}</option>)}
                                            </select>
                                            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600 pointer-events-none" />
                                        </div>
                                        <PrimaryBtn accent="emerald" onClick={handleAddAbx} disabled={!selectedAbxId}>
                                            <Plus className="w-4 h-4" /> Add to Panel
                                        </PrimaryBtn>
                                    </div>
                                </div>

                                <Divider />

                                {/* Register master records */}
                                <div>
                                    <FieldLabel>Register New Master Records</FieldLabel>
                                    <div className="grid grid-cols-2 gap-6">

                                        {/* New organism */}
                                        <div className={`${glass} rounded-xl p-5`}>
                                            <p className="text-[12px] font-semibold text-slate-400 mb-4">New Organism</p>
                                            <form onSubmit={handleCreateOrg} className="space-y-3">
                                                <input
                                                    type="text"
                                                    value={newOrgName}
                                                    onChange={e => setNewOrgName(e.target.value)}
                                                    placeholder="e.g. Klebsiella oxytoca"
                                                    className={inputCls}
                                                />
                                                <PrimaryBtn type="submit" accent="emerald" disabled={!newOrgName.trim()} className="w-full justify-center">
                                                    <Check className="w-3.5 h-3.5" /> Register Organism
                                                </PrimaryBtn>
                                            </form>
                                        </div>

                                        {/* New antibiotic */}
                                        <div className={`${glass} rounded-xl p-5`}>
                                            <p className="text-[12px] font-semibold text-slate-400 mb-4">New Antibiotic</p>
                                            <form onSubmit={handleCreateAbx} className="space-y-3">
                                                <input
                                                    type="text"
                                                    value={newAbxName}
                                                    onChange={e => setNewAbxName(e.target.value)}
                                                    placeholder="Generic name (e.g. Ertapenem)"
                                                    className={inputCls}
                                                />
                                                <div className="flex gap-2">
                                                    <input
                                                        type="text"
                                                        value={newAbxCode}
                                                        onChange={e => setNewAbxCode(e.target.value.toUpperCase())}
                                                        placeholder="Code (e.g. ETP)"
                                                        className={`${inputCls} uppercase w-32`}
                                                    />
                                                    <PrimaryBtn type="submit" accent="emerald" disabled={!newAbxName.trim()} className="flex-1 justify-center">
                                                        <Check className="w-3.5 h-3.5" /> Register
                                                    </PrimaryBtn>
                                                </div>
                                            </form>
                                        </div>
                                    </div>
                                </div>

                                {/* Data policy note */}
                                <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-400/5 border border-amber-400/10">
                                    <AlertCircle className="w-3.5 h-3.5 text-amber-400/60 flex-shrink-0 mt-0.5" />
                                    <p className="text-[11px] text-slate-600 leading-relaxed">
                                        Removing an antibiotic from a panel affects future aggregation only.
                                        All historical surveillance records are preserved permanently.
                                    </p>
                                </div>

                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
        </div>
    );
};

export default MasterDataManager;
