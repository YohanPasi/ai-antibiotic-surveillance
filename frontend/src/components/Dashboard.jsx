import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    AlertTriangle, TrendingUp, PlusCircle,
    Shield, Zap, ArrowUpRight, Calendar, Activity, Building2
} from 'lucide-react';
import AntibiogramTable from './AntibiogramTable';
import ASTEntryForm from './ASTEntryForm';

/* ── Helpers ──────────────────────────────────────────────────────────── */
const fmtIso = (iso, year = false) => {
    if (!iso) return '??';
    return new Date(iso + 'T00:00:00').toLocaleDateString('en-GB',
        year ? { day: '2-digit', month: 'short', year: 'numeric' } : { day: '2-digit', month: 'short' });
};
const fmtWeekRange = (start, year = false) => {
    if (!start) return '?? – ??';
    const end = new Date(new Date(start + 'T00:00:00').getTime() + 6 * 86400000).toISOString().split('T')[0];
    return `${fmtIso(start)} – ${fmtIso(end, year)}`;
};

/* ── Severity ──────────────────────────────────────────────────────────── */
const SEV_STYLES = {
    Critical: { strip: '#ef4444', dot: '#ef4444', text: '#ef4444', darkText: '#f87171', badgeBg: 'rgba(239,68,68,0.1)', badgeBorder: 'rgba(239,68,68,0.25)', label: 'Critical' },
    Warning: { strip: '#f59e0b', dot: '#fbbf24', text: '#d97706', darkText: '#fcd34d', badgeBg: 'rgba(245,158,11,0.1)', badgeBorder: 'rgba(245,158,11,0.25)', label: 'Warning' },
    Normal: { strip: '#10b981', dot: '#34d399', text: '#059669', darkText: '#6ee7b7', badgeBg: 'rgba(16,185,129,0.1)', badgeBorder: 'rgba(16,185,129,0.25)', label: 'Normal' },
};

/* ── Animated counter ─────────────────────────────────────────────────── */
const Counter = ({ value }) => {
    const [n, setN] = useState(0);
    useEffect(() => {
        if (!value) return;
        let v = 0;
        const step = Math.max(1, Math.ceil(value / 24));
        const id = setInterval(() => {
            v = Math.min(v + step, value);
            setN(v);
            if (v >= value) clearInterval(id);
        }, 35);
        return () => clearInterval(id);
    }, [value]);
    return <>{n}</>;
};

const KPI_DATA = (kpis) => [
    { label: 'Active Alerts', value: kpis.total, color: '#a78bfa', topColor: '#7c3aed', icon: Zap, sub: 'Hospital-wide' },
    { label: 'Critical Wards', value: kpis.critical, color: '#f87171', topColor: '#dc2626', icon: AlertTriangle, sub: 'Immediate action' },
    { label: 'Watch Wards', value: kpis.warning, color: '#fbbf24', topColor: '#d97706', icon: TrendingUp, sub: 'Elevated resistance' },
    { label: 'Safe Wards', value: kpis.safe, color: '#34d399', topColor: '#059669', icon: Shield, sub: 'Within normal range' },
];

const KpiStrip = ({ kpis }) => (
    <div className="flex flex-col md:flex-row gap-3 mb-8">
        {KPI_DATA(kpis).map(({ label, value, color, topColor, icon: Icon, sub }, i) => (
            <motion.div
                key={label}
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07, duration: 0.35, ease: 'easeOut' }}
                className={`relative overflow-hidden rounded-[18px] bg-white dark:bg-[#0d1117] border border-slate-200 dark:border-white/10 shadow-sm dark:shadow-none min-w-0 ${i === 0 ? 'md:flex-[1.6]' : 'md:flex-1'}`}
            >
                {/* coloured top accent bar */}
                <div style={{ height: 3, background: `linear-gradient(90deg, ${topColor}, ${color}88)` }} />
                {/* glow spot */}
                <div className="absolute -top-8 -right-8 w-32 h-32 pointer-events-none opacity-50 dark:opacity-100"
                    style={{ background: `radial-gradient(circle, ${color}30 0%, transparent 70%)` }} />
                <div className="p-6 relative z-10">
                    {/* icon + label row */}
                    <div className="flex items-center justify-between mb-5">
                        <span className="text-[10px] font-bold tracking-[0.14em] uppercase text-slate-500 dark:text-slate-400">{sub}</span>
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-white dark:bg-transparent"
                            style={{ background: `${color}14`, border: `1px solid ${color}30` }}>
                            <Icon style={{ color }} className="w-3.5 h-3.5" strokeWidth={1.8} />
                        </div>
                    </div>
                    {/* number */}
                    <div className="font-extrabold leading-none tracking-tight tabular-nums"
                        style={{ fontSize: i === 0 ? 64 : 48, color }}>
                        <Counter value={value} />
                    </div>
                    {/* label */}
                    <p className="text-[13px] font-medium text-slate-500 dark:text-[#64748b] mt-2.5">{label}</p>
                </div>
            </motion.div>
        ))}
    </div>
);

/* ── Ward card ────────────────────────────────────────────────────────── */
const WardCard = ({ row, idx, onClick }) => {
    const sv = SEV_STYLES[row.highest_severity] ?? SEV_STYLES.Normal;
    const total = (row.green || 0) + (row.amber || 0) + (row.red || 0);
    const safePct = total ? (row.green || 0) / total * 100 : 0;
    const warnPct = total ? (row.amber || 0) / total * 100 : 0;
    const critPct = total ? (row.red || 0) / total * 100 : 0;

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08 + idx * 0.05, duration: 0.3 }}
            whileHover={{ y: -2, transition: { duration: 0.15 } }}
            onClick={onClick}
            className="relative overflow-hidden cursor-pointer rounded-2xl bg-white dark:bg-[#0b0f18] border border-slate-200 dark:border-white/5 shadow-sm dark:shadow-none hover:shadow-md transition-shadow"
        >
            {/* left severity strip */}
            <div className="absolute left-0 top-0 bottom-0 w-[3px]" style={{ background: sv.strip }} />

            <div className="pl-5 pr-4 py-4 relative z-10">
                {/* Top: ward name + badge */}
                <div className="flex items-start justify-between mb-3.5">
                    <div>
                        <p className="text-[13px] font-bold text-slate-800 dark:text-slate-200 mb-0.5">
                            {row.ward}
                        </p>
                        {row.active_alerts > 0 && (
                            <p className="text-[11px] font-medium dark:hidden" style={{ color: sv.text }}>
                                {row.active_alerts} alert{row.active_alerts !== 1 ? 's' : ''}
                            </p>
                        )}
                        {row.active_alerts > 0 && (
                            <p className="text-[11px] font-medium hidden dark:block" style={{ color: sv.darkText }}>
                                {row.active_alerts} alert{row.active_alerts !== 1 ? 's' : ''}
                            </p>
                        )}
                    </div>
                    <div className="flex flex-col items-end gap-1.5">
                        <span className="text-[9px] font-extrabold tracking-[0.1em] uppercase px-2 py-0.5 rounded-full"
                            style={{ background: sv.badgeBg, border: `1px solid ${sv.badgeBorder}`, color: sv.darkText }}>
                            {sv.label}
                        </span>
                        <ArrowUpRight className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />
                    </div>
                </div>

                {/* Stacked bar */}
                {total > 0 ? (
                    <>
                        <div className="h-1.5 rounded-full overflow-hidden flex gap-[1px] mb-2.5 bg-slate-100 dark:bg-white/5">
                            {[
                                { pct: safePct, color: '#10b981' },
                                { pct: warnPct, color: '#f59e0b' },
                                { pct: critPct, color: '#ef4444' },
                            ].map((seg, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ width: 0 }}
                                    animate={{ width: `${seg.pct}%` }}
                                    transition={{ delay: 0.4 + idx * 0.04, duration: 0.7, ease: 'easeOut' }}
                                    style={{ height: '100%', background: seg.color, minWidth: seg.pct > 0 ? 2 : 0, flexShrink: 0 }}
                                />
                            ))}
                        </div>
                        <div className="flex gap-4">
                            {[
                                { val: row.green || 0, color: '#34d399', label: 'Safe' },
                                { val: row.amber || 0, color: '#fbbf24', label: 'Watch' },
                                { val: row.red || 0, color: '#f87171', label: 'Alert' },
                            ].map(({ val, color, label }) => (
                                <div key={label} className="flex items-baseline gap-1">
                                    <span className={`text-[13px] font-bold tabular-nums ${val ? '' : 'text-slate-300 dark:text-slate-700'}`}
                                        style={{ color: val ? color : undefined }}>
                                        {val}
                                    </span>
                                    <span className="text-[9px] uppercase tracking-[0.08em] font-semibold text-slate-400 dark:text-slate-500">
                                        {label}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </>
                ) : (
                    <p className="text-[11px] italic text-slate-400 dark:text-slate-600">No data this period</p>
                )}
            </div>
        </motion.div>
    );
};

/* ── Loading ──────────────────────────────────────────────────────────── */
const Loading = () => (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-5">
        <div className="relative w-12 h-12">
            <div className="absolute inset-0 rounded-full border-2 border-emerald-500/30" />
            <div className="absolute inset-0 rounded-full border-t-2 border-emerald-500 animate-spin" />
        </div>
        <div className="text-center">
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">Loading Surveillance</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-500 mt-1">Analysing ward data and AI signals…</p>
        </div>
    </div>
);

/* ── Dashboard ────────────────────────────────────────────────────────── */
const Dashboard = ({ setActiveView, setSelectedWard }) => {
    const [summary, setSummary] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isEntryOpen, setIsEntryOpen] = useState(false);
    const [lastDataWeek, setLastDataWeek] = useState(null);
    const [predictedWeekStart, setPredictedWeekStart] = useState(null);

    const fetchSummary = async () => {
        try {
            const [sRes, aRes] = await Promise.all([
                fetch(`${import.meta.env.VITE_API_URL}/api/dashboard/summary`),
                fetch(`${import.meta.env.VITE_API_URL}/api/analysis/antibiogram`),
            ]);
            const sd = await sRes.json();
            setSummary(sd.hospital_summary ?? []);
            if (aRes.ok) {
                const ad = await aRes.json();
                setLastDataWeek(ad.last_data_week ?? null);
                setPredictedWeekStart(ad.predicted_week_start ?? null);
            }
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetchSummary(); }, []);

    const kpis = useMemo(() => ({
        total: summary.reduce((s, r) => s + (r.active_alerts || 0), 0),
        critical: summary.filter(r => r.highest_severity === 'Critical').length,
        warning: summary.filter(r => r.highest_severity === 'Warning').length,
        safe: summary.filter(r => r.highest_severity === 'Normal').length,
    }), [summary]);

    if (loading) return <Loading />;

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }} className="pb-14">

            {/* ── Header ──────────────────────────────────────────── */}
            <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
                <div>
                    <p className="text-[10px] font-extrabold tracking-[0.2em] uppercase text-emerald-600 dark:text-emerald-500/80 mb-2">
                        AMR Intelligence · Live
                    </p>
                    <h1 className="text-[26px] font-extrabold text-slate-900 dark:text-white tracking-tight leading-none">
                        Hospital Surveillance
                    </h1>
                    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 mt-3">
                        <span className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_6px_#10b981] dark:bg-emerald-400 dark:shadow-[0_0_6px_#34d399]" />
                            Real-time monitoring
                        </span>
                        {lastDataWeek && (
                            <span className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
                                <Calendar className="w-3 h-3" />
                                {fmtWeekRange(lastDataWeek)}
                            </span>
                        )}
                        {predictedWeekStart && (
                            <span className="text-[10px] font-semibold px-2.5 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-500/10 border border-indigo-200 dark:border-indigo-500/25 text-indigo-700 dark:text-indigo-300">
                                AI Forecasting → {fmtWeekRange(predictedWeekStart, true)}
                            </span>
                        )}
                    </div>
                </div>

                <motion.button
                    whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                    onClick={() => setIsEntryOpen(true)}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-[13px] font-semibold text-white bg-indigo-600 hover:bg-indigo-700 shadow-xl shadow-indigo-600/30 transition-colors"
                >
                    <PlusCircle className="w-4 h-4" />
                    New AST Entry
                </motion.button>
            </div>

            {/* ── KPI strip ─────────────────────────────────────── */}
            <KpiStrip kpis={kpis} />

            {/* ── Antibiogram ─────────────────────────────────────── */}
            <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.25 }} className="mb-8">
                <AntibiogramTable />
            </motion.div>

            {/* ── Ward grid ───────────────────────────────────────── */}
            <div>
                <div className="flex items-baseline justify-between mb-5">
                    <div>
                        <h2 className="text-[15px] font-bold text-slate-900 dark:text-slate-100">Ward Risk Overview</h2>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
                            Select a ward to view detailed drug–bug analysis
                        </p>
                    </div>
                    <span className="text-[11px] text-slate-500 dark:text-slate-400">
                        {summary.length} ward{summary.length !== 1 ? 's' : ''}
                    </span>
                </div>

                {summary.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-16 gap-3 bg-white dark:bg-white/5 rounded-2xl border border-slate-200 dark:border-white/5 text-slate-500">
                        <Activity className="w-7 h-7 opacity-30" />
                        <p className="text-[13px]">No ward data available</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5">
                        {summary.map((row, idx) => (
                            <WardCard
                                key={row.ward}
                                row={row}
                                idx={idx}
                                onClick={() => { setSelectedWard(row.ward); setActiveView('ward_detail'); }}
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* ── AST Entry modal ─────────────────────────────────── */}
            <ASTEntryForm
                isOpen={isEntryOpen}
                onClose={() => setIsEntryOpen(false)}
                onEntrySaved={fetchSummary}
                defaultCultureDate={predictedWeekStart}
            />
        </motion.div>
    );
};

export default Dashboard;
