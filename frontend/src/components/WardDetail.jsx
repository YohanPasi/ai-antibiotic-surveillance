import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ArrowLeft, X, Activity, TrendingDown, TrendingUp,
    Minus, FlaskConical, BarChart2, ChevronRight, Info, Calendar, AlertTriangle, Clock
} from 'lucide-react';
import HistoricalChart from './HistoricalChart';
import ProcessControlChart from './ProcessControlChart';
import CockpitPanels from './CockpitPanels';
import AntibiogramTable from './AntibiogramTable';

/* ── Stale-data helpers ────────────────────────────────────────── */
const monthsAgo = (isoDate) => {
    if (!isoDate) return null;
    const diffMs = Date.now() - new Date(isoDate + 'T00:00:00').getTime();
    return Math.floor(diffMs / (1000 * 60 * 60 * 24 * 30.44));
};
const isStale = (isoDate, thresholdMonths = 12) => {
    const m = monthsAgo(isoDate);
    return m !== null && m > thresholdMonths;
};

/* ── Format ISO date for display ───────────────────────────── */
const fmtIso = (iso, year = false) => {
    if (!iso) return '??';
    const opts = year
        ? { day: '2-digit', month: 'short', year: 'numeric' }
        : { day: '2-digit', month: 'short' };
    return new Date(iso + 'T00:00:00').toLocaleDateString('en-GB', opts);
};

/* ── G8 status config (keyed to exact backend strings) ─────────────── */
const statusConfig = {
    // G8 primary alerts — exact backend strings
    RED: { dot: 'bg-red-500', ring: 'ring-red-500/30', text: 'text-red-400', label: 'Critical Breach', badge: 'bg-red-500/10 border-red-500/20 text-red-400', priority: 1 },
    DRIFT_WARNING: { dot: 'bg-orange-400', ring: 'ring-orange-400/30', text: 'text-orange-400', label: 'Drift Warning', badge: 'bg-orange-500/10 border-orange-500/20 text-orange-400', priority: 2 },
    DEGRADED: { dot: 'bg-rose-400', ring: 'ring-rose-400/30', text: 'text-rose-400', label: 'Model Degraded', badge: 'bg-rose-500/10 border-rose-500/20 text-rose-400', priority: 3 },
    BIAS_WARNING: { dot: 'bg-yellow-400', ring: 'ring-yellow-400/30', text: 'text-yellow-400', label: 'Bias Warning', badge: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400', priority: 4 },
    AMBER: { dot: 'bg-amber-400', ring: 'ring-amber-400/30', text: 'text-amber-400', label: 'Watch', badge: 'bg-amber-500/10 border-amber-500/20 text-amber-400', priority: 5 },
    GREEN: { dot: 'bg-emerald-400', ring: 'ring-emerald-400/30', text: 'text-emerald-400', label: 'Normal', badge: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400', priority: 6 },
    INSUFFICIENT_DATA: { dot: 'bg-gray-500', ring: 'ring-gray-500/30', text: 'text-gray-400', label: 'Learning Phase', badge: 'bg-gray-500/10 border-gray-500/20 text-gray-400', priority: 7 },
    // Legacy fallbacks (backward-compat for old endpoints)
    critical: { dot: 'bg-red-500', ring: 'ring-red-500/30', text: 'text-red-400', label: 'Critical', badge: 'bg-red-500/10 border-red-500/20 text-red-400', priority: 1 },
    red: { dot: 'bg-red-500', ring: 'ring-red-500/30', text: 'text-red-400', label: 'Critical', badge: 'bg-red-500/10 border-red-500/20 text-red-400', priority: 1 },
    amber: { dot: 'bg-amber-400', ring: 'ring-amber-400/30', text: 'text-amber-400', label: 'Warning', badge: 'bg-amber-500/10 border-amber-500/20 text-amber-400', priority: 5 },
    'amber-high': { dot: 'bg-amber-400', ring: 'ring-amber-400/30', text: 'text-amber-400', label: 'Elevated', badge: 'bg-amber-500/10 border-amber-500/20 text-amber-400', priority: 5 },
    green: { dot: 'bg-emerald-400', ring: 'ring-emerald-400/30', text: 'text-emerald-400', label: 'Normal', badge: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400', priority: 6 },
};
// Resolve G8 primary_alert → statusConfig entry (new format preferred, old fallback)
const getStatus = (row) => {
    // New backend format: primary_alert field (string like 'RED', 'DRIFT_WARNING')
    const key = row?.primary_alert ?? row?.status ?? 'GREEN';
    return statusConfig[key] ?? statusConfig.GREEN;
};

/* ── trend icon ────────────────────────────────────────────────────── */
const TrendIcon = ({ trend }) => {
    if (trend === '↓') return <TrendingDown className="w-4 h-4 text-red-400" />;
    if (trend === '↑') return <TrendingUp className="w-4 h-4 text-emerald-400" />;
    return <Minus className="w-4 h-4 text-gray-500" />;
};

/* ── stat chip (used in analysis modal) ────────────────────────────── */
const StatChip = ({ label, value, accent }) => (
    <div className={`flex flex-col items-center px-5 py-3 rounded-xl border ${accent} bg-white/[0.03]`}>
        <p className="text-xl font-bold text-white tabular-nums">{value}</p>
        <p className="text-[11px] text-gray-500 mt-0.5 font-medium uppercase tracking-wider">{label}</p>
    </div>
);

/* ── main component ─────────────────────────────────────────────────── */
const WardDetail = ({ wardId, goBack }) => {
    const [details, setDetails] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedTarget, setSelectedTarget] = useState(null);
    const [analysisData, setAnalysisData] = useState(null);
    const [analysisLoading, setAnalysisLoading] = useState(false);
    const [hoveredRow, setHoveredRow] = useState(null);

    useEffect(() => {
        // NF scope: only these two organisms
        const NF_ORGANISMS = ['Pseudomonas aeruginosa', 'Acinetobacter baumannii'];
        fetch(`http://localhost:8000/api/ward/${wardId}/status`)
            .then(res => res.json())
            .then(data => {
                // Frontend safety lock — filter to Non-Fermenters only
                const nfTargets = (data.monitored_targets || []).filter(
                    t => NF_ORGANISMS.includes(t.organism)
                );
                setDetails(nfTargets);
                setLoading(false);
            })
            .catch(err => { console.error(err); setLoading(false); });
    }, [wardId]);

    const handleRowClick = (organism, antibiotic) => {
        setSelectedTarget({ organism, antibiotic });
        setAnalysisLoading(true);
        fetch(`http://localhost:8000/api/analysis/target?ward=${wardId}&organism=${organism}&antibiotic=${antibiotic}`)
            .then(res => res.json())
            .then(data => {
                // ── Phase A: Store the FULL API response — no cherry-picking.
                // Merge baseline into history for chart (backward-compat).
                const merged = (data.history || []).map((h, i) => ({
                    ...h,
                    expected_s: data.baseline?.[i]?.expected_s ?? h.expected_s,
                }));
                const lastEntry = merged.at(-1);
                // Preserve every backend field: primary_alert, secondary_alerts,
                // drift_analysis, model_performance, engine_version, etc.
                setAnalysisData({
                    ...data,
                    history: merged,
                    lastSignalWeek: lastEntry?.week_start_date ?? null,
                });
                setAnalysisLoading(false);
            })
            .catch(err => { console.error(err); setAnalysisLoading(false); });
    };

    const closeAnalysis = () => { setSelectedTarget(null); setAnalysisData(null); };

    /* ── loading ── */
    if (loading) return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
            <div className="relative w-16 h-16">
                <div className="absolute inset-0 rounded-full border-2 border-blue-500/20" />
                <div className="absolute inset-0 rounded-full border-t-2 border-blue-400 animate-spin" />
                <div className="absolute inset-2 rounded-full border-t-2 border-violet-400 animate-spin"
                    style={{ animationDirection: 'reverse', animationDuration: '0.8s' }} />
            </div>
            <p className="text-sm text-gray-500 animate-pulse">Loading ward data…</p>
        </div>
    );

    /* ── KPI summary — G8 hierarchy ── */
    // Count using primary_alert (new) with fallback to status (old endpoint)
    const resolveAlert = (d) => d?.primary_alert ?? d?.status ?? 'GREEN';
    const critCount = details.filter(d => resolveAlert(d) === 'RED').length;
    const driftCount = details.filter(d => resolveAlert(d) === 'DRIFT_WARNING').length;
    const warnCount = details.filter(d => ['AMBER', 'BIAS_WARNING', 'DEGRADED', 'amber', 'amber-high'].includes(resolveAlert(d))).length;
    const downTrends = details.filter(d => d.trend === '↓').length;

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.35 }}
            className="space-y-6 pb-10"
        >
            {/* ── Back + Header ── */}
            <div className="flex items-start justify-between gap-4">
                <div>
                    <button
                        onClick={goBack}
                        className="inline-flex items-center gap-1.5 text-xs font-semibold text-gray-500
                                   hover:text-white transition-colors duration-150 mb-3 group"
                    >
                        <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
                        Back to Overview
                    </button>
                    <p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-400 mb-1">
                        Ward-Level Surveillance
                    </p>
                    <h1 className="text-3xl font-extrabold text-white tracking-tight">
                        Ward {wardId}
                    </h1>
                    <p className="text-gray-400 text-sm mt-1">
                        Click any row to view time-series analysis
                    </p>
                </div>
            </div>

            {/* ── KPI Strip — G8 counts ── */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                    { label: 'Total Targets', value: details.length, accent: 'bg-violet-500', icon: Activity },
                    { label: 'Critical (RED)', value: critCount, accent: 'bg-red-500', icon: TrendingDown },
                    { label: 'Drift / Watch', value: driftCount + warnCount, accent: 'bg-orange-500', icon: BarChart2 },
                    { label: 'Declining', value: downTrends, accent: 'bg-rose-600', icon: TrendingDown },
                ].map(({ label, value, accent, icon: Icon }, i) => (
                    <motion.div
                        key={label}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.07 }}
                        className="relative overflow-hidden rounded-2xl border border-white/5 bg-gray-900/60
                                   backdrop-blur-sm p-5 flex flex-col gap-3 hover:border-white/10
                                   hover:-translate-y-0.5 transition-all duration-300 group"
                    >
                        <div className={`absolute -top-6 -right-6 w-24 h-24 rounded-full blur-3xl opacity-15
                                         group-hover:opacity-25 transition-opacity duration-500 ${accent}`} />
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${accent}
                                         bg-opacity-20 border border-white/10`}>
                            <Icon className="w-5 h-5 text-white" strokeWidth={1.8} />
                        </div>
                        <div>
                            <p className="text-3xl font-bold text-white tracking-tight leading-none">{value}</p>
                            <p className="text-sm font-semibold text-white/70 mt-1">{label}</p>
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* ── Ward Antibiogram ── */}
            <AntibiogramTable wardId={wardId} />

            {/* ── Monitored Targets Table ── */}
            <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.25 }}
                className="rounded-2xl border border-white/5 bg-gray-900/60 backdrop-blur-sm shadow-xl overflow-hidden"
            >
                {/* Card Header */}
                <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-white/5">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20
                                        flex items-center justify-center">
                            <FlaskConical className="w-4 h-4 text-blue-400" strokeWidth={1.8} />
                        </div>
                        <div>
                            <h2 className="text-base font-bold text-white">Monitored Targets</h2>
                            <p className="text-xs text-gray-500 mt-0.5">
                                Organism–antibiotic pairs under active surveillance
                            </p>
                        </div>
                    </div>
                    <span className="text-xs font-semibold text-gray-500 bg-white/5 border border-white/5
                                     px-3 py-1 rounded-full">
                        {details.length} pairs
                    </span>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="text-[11px] uppercase tracking-widest text-gray-500 border-b border-white/5">
                                <th className="px-6 py-3 font-semibold">Organism</th>
                                <th className="px-6 py-3 font-semibold">Antibiotic</th>
                                <th className="px-6 py-3 font-semibold text-center">Current S%</th>
                                <th className="px-6 py-3 font-semibold text-center">Baseline</th>
                                <th className="px-6 py-3 font-semibold text-center">Forecast</th>
                                <th className="px-6 py-3 font-semibold text-center">Trend</th>
                                <th className="px-6 py-3 font-semibold">Status</th>
                                <th className="px-6 py-3 font-semibold">Last Data</th>
                                <th className="px-6 py-3 font-semibold text-right">Analysis</th>
                            </tr>
                        </thead>
                        <tbody>
                            <AnimatePresence>
                                {/* G8-sorted: sort by priority so RED targets float to top */}
                                {[...details]
                                    .sort((a, b) => (getStatus(a).priority ?? 9) - (getStatus(b).priority ?? 9))
                                    .map((row, idx) => {
                                        const sv = getStatus(row);
                                        const isHovered = hoveredRow === idx;
                                        const secondaryAlerts = row.secondary_alerts ?? [];
                                        const isColdStart = (row.primary_alert ?? row.status) === 'INSUFFICIENT_DATA';
                                        return (
                                            <motion.tr
                                                key={`${row.organism}-${row.antibiotic}`}
                                                initial={{ opacity: 0, x: -6 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: idx * 0.045, duration: 0.25 }}
                                                onMouseEnter={() => setHoveredRow(idx)}
                                                onMouseLeave={() => setHoveredRow(null)}
                                                onClick={() => handleRowClick(row.organism, row.antibiotic)}
                                                className="border-b border-white/[0.04] cursor-pointer
                                                       hover:bg-white/[0.03] transition-colors duration-150"
                                            >
                                                {/* Organism */}
                                                <td className="px-6 py-4">
                                                    <span className="font-semibold text-white text-sm italic">
                                                        {row.organism}
                                                    </span>
                                                </td>

                                                {/* Antibiotic */}
                                                <td className="px-6 py-4">
                                                    <span className="font-mono text-gray-300 text-xs bg-white/5
                                                                  border border-white/10 px-2 py-0.5 rounded">
                                                        {row.antibiotic}
                                                    </span>
                                                </td>

                                                {/* Current S% */}
                                                <td className="px-6 py-4 text-center">
                                                    <span className={`text-lg font-bold tabular-nums ${sv.text ?? 'text-white'
                                                        }`}>
                                                        {(row.current_s ?? 0).toFixed(1)}%
                                                    </span>
                                                </td>

                                                {/* Baseline */}
                                                <td className="px-6 py-4 text-center">
                                                    <span className="text-sm text-gray-400 tabular-nums">
                                                        {(row.baseline_s ?? 0).toFixed(1)}%
                                                    </span>
                                                </td>

                                                {/* Forecast */}
                                                <td className="px-6 py-4 text-center">
                                                    {isColdStart ? (
                                                        <span className="text-xs text-gray-600 italic">Learning…</span>
                                                    ) : (
                                                        <span className="text-sm font-semibold text-violet-300 tabular-nums">
                                                            {(row.forecast_s ?? 0).toFixed(1)}%
                                                        </span>
                                                    )}
                                                </td>

                                                {/* Trend */}
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center justify-center">
                                                        <TrendIcon trend={row.trend} />
                                                    </div>
                                                </td>

                                                {/* G8 Primary Alert Badge + Secondary Pills */}
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-col gap-1">
                                                        {/* Primary */}
                                                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full
                                                                      text-[11px] font-bold border ${sv.badge}`}>
                                                            <span className={`w-1.5 h-1.5 rounded-full ${sv.dot}`} />
                                                            {sv.label}
                                                        </span>
                                                        {/* Secondary alerts as small pills */}
                                                        {secondaryAlerts.length > 0 && (
                                                            <div className="flex flex-wrap gap-1 mt-0.5">
                                                                {secondaryAlerts.map(sec => (
                                                                    <span key={sec}
                                                                        className="text-[9px] font-semibold px-1.5 py-0.5 rounded
                                                                               bg-white/5 border border-white/10 text-gray-400"
                                                                    >
                                                                        {sec.replace('_', ' ')}
                                                                    </span>
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>
                                                </td>

                                                {/* Last data week */}
                                                <td className="px-6 py-4">
                                                    {row.last_data_week ? (
                                                        <span style={{
                                                            display: 'inline-flex', alignItems: 'center', gap: 4,
                                                            fontSize: 10, fontWeight: 600, padding: '2px 7px',
                                                            borderRadius: 99,
                                                            background: isStale(row.last_data_week) ? 'rgba(245,158,11,0.1)' : 'rgba(255,255,255,0.04)',
                                                            border: isStale(row.last_data_week) ? '1px solid rgba(245,158,11,0.3)' : '1px solid rgba(255,255,255,0.08)',
                                                            color: isStale(row.last_data_week) ? '#fbbf24' : '#6b7280',
                                                        }}>
                                                            {isStale(row.last_data_week) && <AlertTriangle style={{ width: 9, height: 9 }} />}
                                                            {fmtIso(row.last_data_week, true)}
                                                        </span>
                                                    ) : (
                                                        <span className="text-gray-700 text-xs">—</span>
                                                    )}
                                                </td>

                                                {/* CTA */}
                                                <td className="px-6 py-4 text-right">
                                                    <motion.div
                                                        animate={{ opacity: isHovered ? 1 : 0, x: isHovered ? 0 : 6 }}
                                                        transition={{ duration: 0.15 }}
                                                        className="inline-flex items-center gap-1 text-blue-400 text-xs font-bold"
                                                    >
                                                        Analyse <ChevronRight className="w-3 h-3" />
                                                    </motion.div>
                                                </td>
                                            </motion.tr>
                                        );
                                    })}
                            </AnimatePresence>
                        </tbody>
                    </table>

                    {details.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-16 text-gray-600 gap-3">
                            <Activity className="w-8 h-8 opacity-30" />
                            <p className="text-sm">No monitored targets for this ward</p>
                        </div>
                    )}
                </div>
            </motion.div>

            {/* ── Analysis Modal ── */}
            <AnimatePresence>
                {selectedTarget && (
                    <motion.div
                        key="analysis-backdrop"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4"
                        style={{ background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(10px)' }}
                    >
                        <motion.div
                            key="analysis-modal"
                            initial={{ opacity: 0, scale: 0.96, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.96, y: 20 }}
                            transition={{ duration: 0.25, ease: 'easeOut' }}
                            className="w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl
                                       border border-white/10 bg-gray-950 shadow-2xl overflow-hidden"
                        >
                            {/* Modal Header */}
                            <div className="flex items-start justify-between px-6 py-5 border-b border-white/5
                                            bg-gradient-to-r from-blue-900/20 to-violet-900/20 flex-shrink-0">
                                <div>
                                    <p className="text-xs font-bold uppercase tracking-widest text-blue-400 mb-1">
                                        Sensitivity Pattern Analysis
                                    </p>
                                    <h3 className="text-lg font-bold text-white italic">
                                        {selectedTarget.organism}
                                    </h3>
                                    <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                                        <span className="text-xs font-mono text-gray-400 bg-white/5 border border-white/10
                                                          px-2 py-0.5 rounded">
                                            {selectedTarget.antibiotic}
                                        </span>
                                        <span className="text-gray-600 text-xs">·</span>
                                        <span className="text-xs text-gray-400">Ward {wardId}</span>

                                        {/* Last signal badge — per-target scope */}
                                        {analysisData?.lastSignalWeek && (
                                            <span style={{
                                                display: 'inline-flex', alignItems: 'center', gap: 5,
                                                fontSize: 11, fontWeight: 600, padding: '3px 9px',
                                                borderRadius: 99,
                                                background: isStale(analysisData.lastSignalWeek)
                                                    ? 'rgba(245,158,11,0.12)'
                                                    : 'rgba(59,130,246,0.1)',
                                                border: isStale(analysisData.lastSignalWeek)
                                                    ? '1px solid rgba(245,158,11,0.35)'
                                                    : '1px solid rgba(59,130,246,0.25)',
                                                color: isStale(analysisData.lastSignalWeek) ? '#fbbf24' : '#93c5fd',
                                            }}>
                                                <Clock style={{ width: 11, height: 11 }} />
                                                Last signal: {fmtIso(analysisData.lastSignalWeek, true)}
                                            </span>
                                        )}

                                        {analysisData?.forecast?.predicted_week_start && (
                                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-[11px] font-semibold">
                                                <Calendar className="w-3 h-3" />
                                                Predicting: {fmtIso(analysisData.forecast.predicted_week_start)} – {fmtIso(analysisData.forecast.predicted_week_end, true)}
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <button
                                    onClick={closeAnalysis}
                                    className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5
                                               flex items-center justify-center text-gray-400 hover:text-white
                                               transition-all duration-150 flex-shrink-0"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>

                            {/* Modal Body */}
                            <div className="flex-1 overflow-y-auto p-6 space-y-5">

                                {/* Forecast stat chips */}
                                {analysisData?.forecast && (
                                    <div className="flex items-center gap-3 flex-wrap">
                                        <StatChip
                                            label={analysisData.forecast.predicted_week_start
                                                ? `${fmtIso(analysisData.forecast.predicted_week_start)} – ${fmtIso(analysisData.forecast.predicted_week_end, true)}`
                                                : 'Predicted Next Week'
                                            }
                                            value={`${analysisData.forecast.predicted_s}%`}
                                            accent="border-violet-500/20"
                                        />
                                        {analysisData.history?.length > 0 && (
                                            <StatChip
                                                label="Last Observed"
                                                value={`${analysisData.history.at(-1)?.['S%'] ?? analysisData.history.at(-1)?.observed_s ?? '—'}%`}
                                                accent="border-blue-500/20"
                                            />
                                        )}
                                        <StatChip
                                            label="Data Points"
                                            value={analysisData.history?.length ?? 0}
                                            accent="border-white/10"
                                        />
                                    </div>
                                )}

                                {/* Stale data warning — only shown when last signal > 12 months ago */}
                                {analysisData?.lastSignalWeek && isStale(analysisData.lastSignalWeek) && (
                                    <motion.div
                                        initial={{ opacity: 0, y: -6 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        style={{
                                            display: 'flex', gap: 12, padding: '14px 16px', borderRadius: 12,
                                            background: 'rgba(245,158,11,0.07)',
                                            border: '1px solid rgba(245,158,11,0.25)',
                                        }}>
                                        <AlertTriangle style={{ width: 16, height: 16, color: '#f59e0b', flexShrink: 0, marginTop: 1 }} />
                                        <div>
                                            <p style={{ fontSize: 12, fontWeight: 700, color: '#fbbf24', marginBottom: 4 }}>
                                                Sparse data — last signal {monthsAgo(analysisData.lastSignalWeek)} months ago
                                            </p>
                                            <p style={{ fontSize: 11, color: '#78716c', lineHeight: 1.6 }}>
                                                The hospital dashboard shows <strong style={{ color: '#d6d3d1' }}>global last data week</strong> (all wards combined).
                                                This chart shows data scoped to{' '}
                                                <strong style={{ color: '#d6d3d1' }}>Ward {wardId} · {selectedTarget.organism} · {selectedTarget.antibiotic}</strong>.
                                                This specific combination has not had ≥3 isolates since{' '}
                                                <strong style={{ color: '#fbbf24' }}>{fmtIso(analysisData.lastSignalWeek, true)}</strong>.
                                                The chart is correct — the data is genuinely sparse for this target.
                                            </p>
                                        </div>
                                    </motion.div>
                                )}

                                {/* ── Phase B: Process Control Chart ── */}
                                <ProcessControlChart
                                    history={analysisData?.history}
                                    forecast={analysisData?.forecast}
                                    driftAnalysis={analysisData?.drift_analysis}
                                    modelSwitchEvents={analysisData?.model_switch_events ?? []}
                                    loading={analysisLoading}
                                />

                                {/* ── Phase C: Clinical cockpit panels (G8 translation + diagnostics + governance) ── */}
                                {!analysisLoading && (
                                    <CockpitPanels
                                        driftAnalysis={analysisData?.drift_analysis}
                                        modelPerformance={analysisData?.model_performance}
                                        forecast={analysisData?.forecast}
                                        organism={selectedTarget?.organism}
                                        antibiotic={selectedTarget?.antibiotic}
                                        ward={wardId}
                                    />
                                )}

                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default WardDetail;
