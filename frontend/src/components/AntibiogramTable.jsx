import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Cpu, FlaskConical, TrendingUp, Calendar } from 'lucide-react';
import Sparkline from './Sparkline';

/* ── Format an ISO date string (YYYY-MM-DD) nicely for display ────── */
const fmtApiDate = (isoStr) => {
    if (!isoStr) return '??';
    const d = new Date(isoStr + 'T00:00:00');
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
};

const fmtPredRange = (isoStart) => {
    if (!isoStart) return '?? – ??';
    const start = new Date(isoStart + 'T00:00:00');
    const end = new Date(start.getTime() + 6 * 86400000);
    const fmt = (d) => d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
    const fmtFull = (d) => d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    return `${fmt(start)} – ${fmtFull(end)}`;
};

/* ── colour helpers ─────────────────────────────────────────────────── */
const cellColour = (value) => {
    if (value >= 80) return {
        bg: 'bg-emerald-50 dark:bg-emerald-500/10',
        border: 'border-emerald-200 dark:border-emerald-500/20',
        text: 'text-emerald-700 dark:text-emerald-300',
        glow: 'shadow-emerald-500/10',
    };
    if (value >= 60) return {
        bg: 'bg-amber-50 dark:bg-amber-500/10',
        border: 'border-amber-200 dark:border-amber-500/20',
        text: 'text-amber-700 dark:text-amber-300',
        glow: 'shadow-amber-500/10',
    };
    return {
        bg: 'bg-red-50 dark:bg-red-500/10',
        border: 'border-red-200 dark:border-red-500/20',
        text: 'text-red-700 dark:text-red-300',
        glow: 'shadow-red-500/10',
    };
};

/* ── component ──────────────────────────────────────────────────────── */
const AntibiogramTable = ({ wardId }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [viewMode, setViewMode] = useState('current');
    const [lastDataWeek, setLastDataWeek] = useState(null);
    const [predictedWeekStart, setPredictedWeekStart] = useState(null);

    useEffect(() => {
        setLoading(true);
        const url = wardId
            ? `http://localhost:8000/api/analysis/antibiogram?ward=${wardId}`
            : `http://localhost:8000/api/analysis/antibiogram`;

        fetch(url)
            .then(res => res.json())
            .then(resData => {
                setData(resData);
                setLastDataWeek(resData.last_data_week || null);
                setPredictedWeekStart(resData.predicted_week_start || null);
                setLoading(false);
            })
            .catch(err => { console.error(err); setLoading(false); });
    }, [wardId]);

    if (loading) return (
        <div className="rounded-2xl border border-slate-200 dark:border-white/5 bg-white/80 dark:bg-gray-900/60 p-8 flex items-center gap-3 text-slate-500 dark:text-gray-500 text-sm mb-7">
            <span className="w-4 h-4 rounded-full border-t-2 border-blue-400 animate-spin" />
            Loading Antibiogram…
        </div>
    );

    if (!data || !data.matrix) return (
        <div className="rounded-2xl border border-slate-200 dark:border-white/5 bg-white/80 dark:bg-gray-900/60 p-8 text-slate-600 dark:text-gray-600 text-sm mb-7">
            No antibiogram data available.
        </div>
    );

    const { matrix, antibiotics, scope } = data;
    // ── Frontend safety lock: Non-Fermenters scope ───────────────────
    const NF_ORGANISMS = ['Pseudomonas aeruginosa', 'Acinetobacter baumannii'];
    const organisms = Object.keys(matrix)
        .filter(org => NF_ORGANISMS.includes(org))
        .sort();

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.2 }}
            className="rounded-2xl border border-slate-200 dark:border-white/5 bg-white/80 dark:bg-gray-900/60 backdrop-blur-sm shadow-xl overflow-hidden mb-7"
        >
            {/* ── Card Header ── */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 px-6 pt-6 pb-4 border-b border-slate-200 dark:border-white/5">
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
                        <FlaskConical className="w-4 h-4 text-violet-400" strokeWidth={1.8} />
                    </div>
                    <div>
                        <h2 className="text-base font-bold text-slate-900 dark:text-white">{scope} Antibiogram</h2>
                        {viewMode === 'current' ? (
                            <p className="text-xs text-slate-500 dark:text-gray-500 mt-0.5 flex items-center gap-1.5">
                                <Calendar className="w-3 h-3" />
                                Last data week:
                                <span className="text-blue-400 font-semibold ml-1">
                                    {lastDataWeek ? fmtApiDate(lastDataWeek) : 'Loading...'}
                                </span>
                                <span className="text-slate-600 dark:text-gray-600">· Cumulative observed % susceptible</span>
                            </p>
                        ) : (
                            <p className="text-xs mt-0.5 flex items-center gap-1.5">
                                <Calendar className="w-3 h-3 text-purple-400" />
                                <span className="text-purple-300 font-semibold">Predicted:</span>
                                <span className="text-purple-400 font-bold">
                                    {fmtPredRange(predictedWeekStart)}
                                </span>
                                <span className="ml-1 px-1.5 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-[9px] font-bold tracking-wide">NEXT WEEK</span>
                            </p>
                        )}
                    </div>
                </div>

                {/* Toggle */}
                <div className="flex bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/5 rounded-xl p-1 gap-1 self-start md:self-auto">
                    <button
                        onClick={() => setViewMode('current')}
                        className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200
                            ${viewMode === 'current'
                                ? 'bg-blue-600 text-slate-900 dark:text-white shadow-lg shadow-blue-900/40'
                                : 'text-slate-500 dark:text-gray-400 hover:text-slate-900 dark:text-white hover:bg-slate-100 dark:bg-white/5'}`}
                    >
                        <TrendingUp className="w-3 h-3" /> Current Observed
                    </button>
                    <button
                        onClick={() => setViewMode('predicted')}
                        className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200
                            ${viewMode === 'predicted'
                                ? 'bg-purple-600 text-slate-900 dark:text-white shadow-lg shadow-purple-900/40'
                                : 'text-slate-500 dark:text-gray-400 hover:text-slate-900 dark:text-white hover:bg-slate-100 dark:bg-white/5'}`}
                    >
                        <Cpu className="w-3 h-3" /> AI Predicted
                    </button>
                </div>
            </div>

            {/* ── Table ── */}
            <div className="overflow-x-auto">
                <table className="w-full text-center text-sm border-collapse">
                    <thead>
                        <tr>
                            <th className="px-5 py-3 text-left text-[11px] uppercase tracking-widest text-slate-500 dark:text-gray-500 font-semibold
                                           sticky left-0 z-10 bg-white/90 dark:bg-gray-900/80 backdrop-blur-sm border-b border-slate-200 dark:border-white/5 min-w-[180px]">
                                Organism
                            </th>
                            {antibiotics.map(abx => (
                                <th key={abx}
                                    className="px-3 py-3 text-[11px] uppercase tracking-wider text-slate-500 dark:text-gray-500 font-semibold
                                               border-b border-slate-200 dark:border-white/5 bg-slate-50 dark:bg-gray-900/40 min-w-[90px] whitespace-nowrap">
                                    {abx}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {organisms.map((org, oIdx) => (
                            <motion.tr
                                key={org}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: oIdx * 0.05 }}
                                className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors"
                            >
                                <td className="px-5 py-3 text-left font-semibold text-slate-900 dark:text-white text-sm
                                               sticky left-0 bg-white/90 dark:bg-gray-900/80 backdrop-blur-sm border-r border-slate-200 dark:border-white/5 italic">
                                    {org}
                                </td>
                                {antibiotics.map(abx => {
                                    const cellData = matrix[org][abx];

                                    if (!cellData) return (
                                        <td key={abx} className="px-2 py-2">
                                            <span className="text-slate-400 dark:text-gray-700 text-xs">—</span>
                                        </td>
                                    );

                                    const val = viewMode === 'current' ? cellData.current : cellData.predicted;
                                    const hasForecast = cellData.has_forecast !== false;
                                    const forecastMethod = cellData.forecast_method;
                                    const history = cellData.history || [];

                                    if (viewMode === 'predicted' && !hasForecast) {
                                        return (
                                            <td key={abx} className="px-2 py-2">
                                                <div className="flex flex-col items-center justify-center h-14 rounded-lg border border-dashed border-slate-300 dark:border-white/10 bg-white/[0.02]">
                                                    <span className="text-[10px] text-slate-600 dark:text-gray-600 leading-tight text-center">Insufficient<br />Data</span>
                                                </div>
                                            </td>
                                        );
                                    }

                                    const c = cellColour(val);
                                    return (
                                        <td key={abx} className="px-2 py-2">
                                            <div className={`flex flex-col items-center justify-center h-14 rounded-lg border
                                                            ${c.bg} ${c.border} shadow-sm ${c.glow} transition-all duration-300`}>
                                                <span className={`text-sm font-bold tabular-nums ${c.text}`}>
                                                    {val.toFixed(0)}%
                                                </span>

                                                {viewMode === 'current' && history.length > 1 && (
                                                    <div className="mt-0.5 opacity-70">
                                                        <Sparkline data={history} />
                                                    </div>
                                                )}

                                                {viewMode === 'predicted' && forecastMethod && (
                                                    <span className={`text-[9px] mt-0.5 font-bold tracking-wide px-1.5 py-0.5 rounded-full
                                                        ${forecastMethod === 'LSTM'
                                                            ? 'bg-purple-500/20 text-purple-300'
                                                            : 'bg-blue-500/20 text-blue-300'}`}>
                                                        {forecastMethod === 'LSTM' ? 'AI' : 'Trend'}
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                    );
                                })}
                            </motion.tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* ── Legend ── */}
            <div className="flex items-center justify-end gap-4 px-6 py-3 border-t border-slate-200 dark:border-white/5 text-[11px] text-slate-500 dark:text-gray-500">
                <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded bg-emerald-500/20 border border-emerald-500/30" />
                    Substantial (&gt;80%)
                </span>
                <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded bg-amber-500/20 border border-amber-500/30" />
                    Moderate (60–80%)
                </span>
                <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded bg-red-500/20 border border-red-500/30" />
                    Resistant (&lt;60%)
                </span>
            </div>
        </motion.div>
    );
};

export default AntibiogramTable;
