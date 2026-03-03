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

/* ── Severity — pure inline styles, no dynamic Tailwind ──────────────── */
const SEV_STYLES = {
    Critical: { strip: '#ef4444', dot: '#ef4444', text: '#f87171', badgeBg: 'rgba(239,68,68,0.1)', badgeBorder: 'rgba(239,68,68,0.25)', label: 'Critical' },
    Warning: { strip: '#f59e0b', dot: '#fbbf24', text: '#fcd34d', badgeBg: 'rgba(245,158,11,0.1)', badgeBorder: 'rgba(245,158,11,0.25)', label: 'Warning' },
    Normal: { strip: '#10b981', dot: '#34d399', text: '#6ee7b7', badgeBg: 'rgba(16,185,129,0.1)', badgeBorder: 'rgba(16,185,129,0.25)', label: 'Normal' },
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
    <div style={{ display: 'flex', gap: 12, marginBottom: 32 }}>
        {KPI_DATA(kpis).map(({ label, value, color, topColor, icon: Icon, sub }, i) => (
            <motion.div
                key={label}
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07, duration: 0.35, ease: 'easeOut' }}
                style={{
                    flex: i === 0 ? '1.6' : '1',
                    minWidth: 0,
                    background: '#0d1117',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 18,
                    overflow: 'hidden',
                    position: 'relative',
                }}>
                {/* coloured top accent bar */}
                <div style={{ height: 3, background: `linear-gradient(90deg, ${topColor}, ${color}88)` }} />
                {/* glow spot */}
                <div style={{
                    position: 'absolute', top: -30, right: -30, width: 130, height: 130,
                    background: `radial-gradient(circle, ${color}18 0%, transparent 70%)`,
                    pointerEvents: 'none',
                }} />
                <div style={{ padding: '22px 24px 22px 24px' }}>
                    {/* icon + label row */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                        <span style={{
                            fontSize: 10, fontWeight: 700, letterSpacing: '0.14em',
                            textTransform: 'uppercase', color: '#374151'
                        }}>{sub}</span>
                        <div style={{
                            width: 30, height: 30, borderRadius: 8,
                            background: `${color}14`,
                            border: `1px solid ${color}30`,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                            <Icon style={{ width: 13, height: 13, color }} strokeWidth={1.8} />
                        </div>
                    </div>
                    {/* number */}
                    <div style={{
                        fontSize: i === 0 ? 64 : 48,
                        fontWeight: 800,
                        color,
                        lineHeight: 1,
                        letterSpacing: '-2px',
                        fontVariantNumeric: 'tabular-nums',
                    }}>
                        <Counter value={value} />
                    </div>
                    {/* label */}
                    <p style={{ fontSize: 13, color: '#64748b', marginTop: 10, fontWeight: 500 }}>{label}</p>
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
            style={{
                background: '#0b0f18',
                border: `1px solid rgba(255,255,255,0.07)`,
                borderRadius: 16,
                overflow: 'hidden',
                cursor: 'pointer',
                position: 'relative',
            }}>

            {/* left severity strip */}
            <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: sv.strip }} />

            <div style={{ paddingLeft: 20, paddingRight: 16, paddingTop: 16, paddingBottom: 16 }}>

                {/* Top: ward name + badge */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 14 }}>
                    <div>
                        <p style={{ fontSize: 13, fontWeight: 700, color: '#e2e8f0', marginBottom: 2 }}>
                            {row.ward}
                        </p>
                        {row.active_alerts > 0 && (
                            <p style={{ fontSize: 11, color: sv.text }}>
                                {row.active_alerts} alert{row.active_alerts !== 1 ? 's' : ''}
                            </p>
                        )}
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                        <span style={{
                            fontSize: 9, fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase',
                            padding: '3px 8px', borderRadius: 99,
                            background: sv.badgeBg, border: `1px solid ${sv.badgeBorder}`, color: sv.text,
                        }}>
                            {sv.label}
                        </span>
                        <ArrowUpRight style={{ width: 13, height: 13, color: '#334155' }} />
                    </div>
                </div>

                {/* Stacked bar */}
                {total > 0 ? (
                    <>
                        <div style={{
                            height: 6, borderRadius: 99, overflow: 'hidden', background: 'rgba(255,255,255,0.05)',
                            display: 'flex', gap: 1, marginBottom: 10
                        }}>
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
                        <div style={{ display: 'flex', gap: 16 }}>
                            {[
                                { val: row.green || 0, color: '#34d399', label: 'Safe' },
                                { val: row.amber || 0, color: '#fbbf24', label: 'Watch' },
                                { val: row.red || 0, color: '#f87171', label: 'Alert' },
                            ].map(({ val, color, label }) => (
                                <div key={label} style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
                                    <span style={{
                                        fontSize: 13, fontWeight: 700, color: val ? color : '#1e293b',
                                        fontVariantNumeric: 'tabular-nums'
                                    }}>{val}</span>
                                    <span style={{
                                        fontSize: 9, color: '#334155', textTransform: 'uppercase',
                                        letterSpacing: '0.08em', fontWeight: 600
                                    }}>{label}</span>
                                </div>
                            ))}
                        </div>
                    </>
                ) : (
                    <p style={{ fontSize: 11, color: '#1e293b', fontStyle: 'italic' }}>No data this period</p>
                )}
            </div>
        </motion.div>
    );
};

/* ── Loading ──────────────────────────────────────────────────────────── */
const Loading = () => (
    <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        minHeight: '60vh', gap: 20
    }}>
        <div style={{ position: 'relative', width: 48, height: 48 }}>
            <div style={{
                position: 'absolute', inset: 0, borderRadius: '50%',
                border: '2px solid rgba(16,185,129,0.3)'
            }} />
            <div style={{
                position: 'absolute', inset: 0, borderRadius: '50%',
                borderTop: '2px solid #10b981', animation: 'spin 1s linear infinite'
            }} />
        </div>
        <div style={{ textAlign: 'center' }}>
            <p style={{ fontSize: 14, color: '#cbd5e1', fontWeight: 600 }}>Loading Surveillance</p>
            <p style={{ fontSize: 11, color: '#374151', marginTop: 4 }}>Analysing ward data and AI signals…</p>
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
            <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 32 }}>
                <div>
                    <p style={{
                        fontSize: 10, fontWeight: 800, letterSpacing: '0.2em', textTransform: 'uppercase',
                        color: 'rgba(52,211,153,0.6)', marginBottom: 8
                    }}>
                        AMR Intelligence · Live
                    </p>
                    <h1 style={{ fontSize: 26, fontWeight: 800, color: '#fff', letterSpacing: '-0.5px', lineHeight: 1 }}>
                        Hospital Surveillance
                    </h1>
                    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '8px 20px', marginTop: 12 }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#475569' }}>
                            <span style={{
                                width: 7, height: 7, borderRadius: '50%', background: '#34d399',
                                boxShadow: '0 0 6px #34d399', display: 'inline-block'
                            }} />
                            Real-time monitoring
                        </span>
                        {lastDataWeek && (
                            <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#475569' }}>
                                <Calendar style={{ width: 11, height: 11 }} />
                                {fmtWeekRange(lastDataWeek)}
                            </span>
                        )}
                        {predictedWeekStart && (
                            <span style={{
                                fontSize: 10, fontWeight: 600, padding: '3px 10px', borderRadius: 99,
                                background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.25)',
                                color: '#a5b4fc'
                            }}>
                                AI Forecasting → {fmtWeekRange(predictedWeekStart, true)}
                            </span>
                        )}
                    </div>
                </div>

                <motion.button
                    whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                    onClick={() => setIsEntryOpen(true)}
                    style={{
                        display: 'flex', alignItems: 'center', gap: 8, padding: '10px 18px',
                        borderRadius: 12, fontSize: 13, fontWeight: 600, color: '#fff',
                        background: '#4f46e5', border: 'none', cursor: 'pointer',
                        boxShadow: '0 4px 24px rgba(79,70,229,0.35)'
                    }}>
                    <PlusCircle style={{ width: 16, height: 16 }} />
                    New AST Entry
                </motion.button>
            </div>

            {/* ── KPI strip ─────────────────────────────────────── */}
            <KpiStrip kpis={kpis} />

            {/* ── Antibiogram ─────────────────────────────────────── */}
            <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.25 }} style={{ marginBottom: 32 }}>
                <AntibiogramTable />
            </motion.div>

            {/* ── Ward grid ───────────────────────────────────────── */}
            <div>
                <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 20 }}>
                    <div>
                        <h2 style={{ fontSize: 15, fontWeight: 700, color: '#f1f5f9' }}>Ward Risk Overview</h2>
                        <p style={{ fontSize: 11, color: '#334155', marginTop: 3 }}>
                            Select a ward to view detailed drug–bug analysis
                        </p>
                    </div>
                    <span style={{ fontSize: 11, color: '#334155' }}>
                        {summary.length} ward{summary.length !== 1 ? 's' : ''}
                    </span>
                </div>

                {summary.length === 0 ? (
                    <div style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center',
                        justifyContent: 'center', padding: '64px 0', gap: 12,
                        background: 'rgba(255,255,255,0.01)', borderRadius: 16,
                        border: '1px solid rgba(255,255,255,0.05)', color: '#1e293b'
                    }}>
                        <Activity style={{ width: 28, height: 28, opacity: 0.3 }} />
                        <p style={{ fontSize: 13 }}>No ward data available</p>
                    </div>
                ) : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 14 }}>
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
