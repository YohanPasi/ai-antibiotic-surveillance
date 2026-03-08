import React, { useState, useEffect } from 'react';

// ── Stat card ──────────────────────────────────────────────────────────────
const Stat = ({ label, value, unit, status, note }) => {
    const colors = {
        OK: 'text-green-400  border-green-700  bg-green-900/20',
        WARNING: 'text-amber-400  border-amber-700  bg-amber-900/20',
        CRITICAL: 'text-red-400    border-red-700    bg-red-900/20',
        INFO: 'text-blue-400   border-blue-700   bg-blue-900/20',
    }[status] || 'text-slate-300 border-slate-600 bg-slate-700/30';

    return (
        <div className={`rounded-lg border p-4 ${colors}`}>
            <p className="text-xs font-medium text-slate-400 mb-1">{label}</p>
            <p className="text-2xl font-bold">
                {value}<span className="text-sm font-normal text-slate-500 ml-1">{unit}</span>
            </p>
            {note && <p className="text-xs text-slate-500 mt-1 leading-snug">{note}</p>}
        </div>
    );
};

// ── Bar row ────────────────────────────────────────────────────────────────
const BarRow = ({ label, pct, color }) => (
    <div>
        <div className="flex justify-between text-xs text-slate-400 mb-1">
            <span>{label}</span>
            <span className="font-medium">{(pct * 100).toFixed(1)}%</span>
        </div>
        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct * 100}%`, backgroundColor: color }} />
        </div>
    </div>
);

// ── Record Action Modal ────────────────────────────────────────────────────
const ActionModal = ({ onClose }) => {
    const [form, setForm] = useState({ action: 'MONITOR', reason: '', notes: '' });

    const handleSubmit = e => {
        e.preventDefault();
        alert('Decision will be recorded.');
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60">
            <div className="w-full max-w-md bg-slate-800 border border-slate-700 rounded-xl shadow-2xl overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-700 flex items-center justify-between">
                    <div>
                        <h3 className="text-sm font-semibold text-slate-200">Record Quality Action</h3>
                        <p className="text-xs text-slate-500 mt-0.5">This entry cannot be deleted once saved</p>
                    </div>
                    <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                <form onSubmit={handleSubmit} className="p-5 space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">What action is needed?</label>
                        <select
                            value={form.action}
                            onChange={e => setForm(p => ({ ...p, action: e.target.value }))}
                            className="w-full bg-slate-700 border border-slate-600 text-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="MONITOR">No change needed — continue monitoring</option>
                            <option value="RETRAIN_REVIEW">Request expert review of the screening tool</option>
                            <option value="DISABLE_MODULE">Suspend screening until reviewed</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Reason for this action</label>
                        <input
                            className="w-full bg-slate-700 border border-slate-600 text-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-500"
                            placeholder="e.g. Rule-out accuracy dropped below 95%"
                            value={form.reason}
                            onChange={e => setForm(p => ({ ...p, reason: e.target.value }))}
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Additional details</label>
                        <textarea
                            className="w-full bg-slate-700 border border-slate-600 text-slate-200 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-slate-500 resize-none"
                            placeholder="Detailed justification..."
                            rows={3}
                            value={form.notes}
                            onChange={e => setForm(p => ({ ...p, notes: e.target.value }))}
                            required
                        />
                    </div>
                    <div className="flex gap-3 pt-1">
                        <button type="button" onClick={onClose}
                            className="flex-1 py-2.5 rounded-lg text-sm font-medium text-slate-400 bg-slate-700 hover:bg-slate-600 border border-slate-600 transition-colors">
                            Cancel
                        </button>
                        <button type="submit"
                            className="flex-1 py-2.5 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors">
                            Save Record
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// ── Main Dashboard ─────────────────────────────────────────────────────────
const MRSAPerformanceDashboard = () => {
    const [summary, setSummary] = useState(null);
    const [heatmap, setHeatmap] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showModal, setShowModal] = useState(false);

    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    useEffect(() => { fetchData(); }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [sumRes, heatRes] = await Promise.all([
                fetch(`${API_URL}/api/mrsa/analytics/summary`),
                fetch(`${API_URL}/api/mrsa/analytics/heatmap`),
            ]);
            if (!sumRes.ok || !heatRes.ok) throw new Error('Failed to load analytics data.');
            setSummary(await sumRes.json());
            setHeatmap(await heatRes.json());
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center py-20 text-slate-500 text-sm gap-2">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Loading dashboard...
        </div>
    );

    if (error) return (
        <div className="p-4 rounded-lg bg-red-900/20 border border-red-700 text-red-300 text-sm">{error}</div>
    );

    const { safety, stewardship, model_health, governance_status } = summary;
    const isActive = governance_status === 'ACTIVE';

    return (
        <div className="space-y-6">

            {/* Page header */}
            <div className="flex flex-wrap items-center gap-3">
                <div>
                    <h1 className="text-xl font-semibold text-white">MRSA Screening — Quality & Safety</h1>
                    <p className="text-sm text-slate-400 mt-0.5">Monthly performance review for the MRSA screening tool</p>
                </div>
                <div className="ml-auto flex items-center gap-2">
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border ${isActive ? 'bg-green-900/20 border-green-700 text-green-400' : 'bg-red-900/20 border-red-700 text-red-400'}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-green-400' : 'bg-red-400'}`} />
                        {isActive ? 'Screening Active' : 'Review Required'}
                    </span>
                    <button
                        onClick={() => setShowModal(true)}
                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-700 hover:bg-slate-600 border border-slate-600 transition-colors"
                    >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        Record Action
                    </button>
                    <button onClick={fetchData} className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-700 transition-colors">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                    </button>
                </div>
            </div>

            {/* ── KPI Stats ── */}
            <section>
                <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Patient Safety & Antibiotic Use</h2>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <Stat
                        label="Rule-Out Accuracy (NPV)"
                        value={safety.formatted_npv.value}
                        unit="%"
                        status={safety.formatted_npv.status}
                        note="Target ≥ 95%. Lower = missed MRSA cases."
                    />
                    <Stat
                        label="Detection Rate"
                        value={safety.formatted_sensitivity.value}
                        unit="%"
                        status={safety.formatted_sensitivity.status}
                        note="Target ≥ 90%. How often MRSA is correctly identified."
                    />
                    <Stat
                        label="Missed MRSA Cases"
                        value={safety.false_negatives_count}
                        unit="cases"
                        status={safety.false_negatives_count > 0 ? 'CRITICAL' : 'OK'}
                        note="MRSA positive cases the screening missed. Target: 0."
                    />
                    <Stat
                        label="Antibiotic Days Saved"
                        value={Math.round(stewardship.vanco_days_saved)}
                        unit="days"
                        status="INFO"
                        note={`Est. vancomycin days avoided across ${stewardship.early_detection_count} cleared patients.`}
                    />
                </div>
            </section>

            {/* ── Ward Risk + Method Performance ── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

                {/* Ward Risk Table */}
                <div className="lg:col-span-2 bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
                    <div className="px-5 py-4 border-b border-slate-700">
                        <h3 className="text-sm font-semibold text-slate-200">Ward Risk Summary</h3>
                        <p className="text-xs text-slate-500 mt-0.5">Last 14 days — % high-risk specimens per ward</p>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-slate-700/50">
                                <tr>
                                    {['Ward', 'High-risk cases (%)', 'Trend', 'Status'].map(h => (
                                        <th key={h} className="px-4 py-3 text-left text-xs font-medium text-slate-400">{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {heatmap.length === 0 ? (
                                    <tr><td colSpan={4} className="px-4 py-8 text-center text-slate-500 text-sm">No recent prediction data</td></tr>
                                ) : (
                                    heatmap.map((w, i) => {
                                        const alertStyle = {
                                            HIGH: 'text-red-400   bg-red-900/20   border-red-700',
                                            MODERATE: 'text-amber-400 bg-amber-900/20 border-amber-700',
                                            LOW: 'text-green-400 bg-green-900/20 border-green-700',
                                        }[w.alert_level] || 'text-slate-400 bg-slate-700 border-slate-600';
                                        const barColor = { HIGH: '#ef4444', MODERATE: '#f59e0b', LOW: '#22c55e' }[w.alert_level] || '#64748b';
                                        return (
                                            <tr key={i} className={`border-t border-slate-700 ${i % 2 === 1 ? 'bg-slate-700/20' : ''} hover:bg-slate-700/40 transition-colors`}>
                                                <td className="px-4 py-3 font-medium text-slate-200">{w.ward}</td>
                                                <td className="px-4 py-3">
                                                    <div className="flex items-center gap-2">
                                                        <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden" style={{ minWidth: '60px' }}>
                                                            <div className="h-full rounded-full" style={{ width: `${w.red_rate}%`, backgroundColor: barColor }} />
                                                        </div>
                                                        <span className="text-xs font-medium text-slate-300 w-8 text-right">{w.red_rate}%</span>
                                                    </div>
                                                </td>
                                                <td className="px-4 py-3 text-xs text-slate-500">{w.trend}</td>
                                                <td className="px-4 py-3">
                                                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${alertStyle}`}>
                                                        {w.alert_level}
                                                    </span>
                                                </td>
                                            </tr>
                                        );
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Method Performance */}
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 flex flex-col gap-4">
                    <div>
                        <h3 className="text-sm font-semibold text-slate-200">Screening Method Performance</h3>
                        <p className="text-xs text-slate-500 mt-0.5">Last 30 days</p>
                    </div>

                    {model_health && Object.keys(model_health).length > 0 ? (
                        <div className="space-y-4">
                            <BarRow label="Overall (combined assessment)" pct={model_health.consensus_acc || 0} color="#22c55e" />
                            <BarRow label="Primary screening method" pct={model_health.rf_acc || 0} color="#3b82f6" />
                            <BarRow label="Confirmatory method" pct={model_health.xgb_acc || 0} color="#a78bfa" />
                        </div>
                    ) : (
                        <p className="text-xs text-slate-500 text-center py-4">No validation data available yet</p>
                    )}

                    <div className="mt-auto p-3 rounded-lg bg-slate-700/50 border border-slate-600">
                        <p className="text-xs text-slate-400 leading-relaxed">
                            <strong className="text-slate-300">Note:</strong> Three separate methods run each time. The combined result shown to clinical staff is the safest combined estimate.
                        </p>
                    </div>
                </div>
            </div>

            {showModal && <ActionModal onClose={() => setShowModal(false)} />}
        </div>
    );
};

export default MRSAPerformanceDashboard;
