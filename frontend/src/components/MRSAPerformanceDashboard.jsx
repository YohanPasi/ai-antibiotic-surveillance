import React, { useState, useEffect } from 'react';
import { Shield, Pill, Activity, AlertTriangle, CheckCircle, TrendingUp, TrendingDown, Minus, Gavel } from 'lucide-react';

const KPICard = ({ title, value, unit, status, trend, icon: Icon, subtext }) => {
    const statusColors = {
        "OK": "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        "WARNING": "bg-amber-500/10 text-amber-400 border-amber-500/20",
        "CRITICAL": "bg-red-500/10 text-red-400 border-red-500/20",
        "INFO": "bg-blue-500/10 text-blue-400 border-blue-500/20"
    };

    const colorClass = statusColors[status] || statusColors["INFO"];

    return (
        <div className={`p-6 rounded-xl border ${colorClass} backdrop-blur-sm relative overflow-hidden`}>
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h3 className="text-sm font-medium opacity-80 uppercase tracking-wider">{title}</h3>
                    <div className="mt-2 flex items-baseline gap-2">
                        <span className="text-3xl font-bold">{value}</span>
                        <span className="text-sm opacity-60">{unit}</span>
                    </div>
                </div>
                <div className={`p-3 rounded-lg bg-white/5`}>
                    <Icon size={24} />
                </div>
            </div>

            {(trend || subtext) && (
                <div className="flex items-center gap-2 text-sm opacity-70 mt-2">
                    {trend === "UP" && <TrendingUp size={16} />}
                    {trend === "DOWN" && <TrendingDown size={16} />}
                    {trend === "STABLE" && <Minus size={16} />}
                    <span>{subtext || trend}</span>
                </div>
            )}
        </div>
    );
};

const MRSAPerformanceDashboard = () => {
    const [summary, setSummary] = useState(null);
    const [heatmap, setHeatmap] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showLogModal, setShowLogModal] = useState(false);

    // Config Base URL
    const API_URL = import.meta.env.VITE_API_URL;

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [sumRes, heatRes] = await Promise.all([
                fetch(`${API_URL}/api/mrsa/analytics/summary`),
                fetch(`${API_URL}/api/mrsa/analytics/heatmap`)
            ]);

            if (!sumRes.ok || !heatRes.ok) throw new Error("Failed to fetch analytics");

            const sumData = await sumRes.json();
            const heatData = await heatRes.json();

            setSummary(sumData);
            setHeatmap(heatData);
        } catch (err) {
            console.error(err);
            setError("Failed to load dashboard data. Ensure backend is running.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-8 text-slate-400 animate-pulse">Loading Governance Dashboard...</div>;
    if (error) return <div className="p-8 text-red-400 bg-red-900/10 border border-red-500/20 rounded-xl">{error}</div>;

    const { safety, stewardship, model_health, governance_status } = summary;

    return (
        <div className="space-y-8 p-6 pb-20 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-slate-100 flex items-center gap-3">
                        <Shield className="text-emerald-400" />
                        MRSA Governance & Performance
                    </h1>
                    <p className="text-slate-400 mt-1">
                        Stage E Monitoring Layer • <span className="text-emerald-400">Baseline Locked v1.0</span>
                    </p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => setShowLogModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 transition-colors"
                    >
                        <Gavel size={18} />
                        Log Decision
                    </button>
                    <div className={`px-4 py-2 rounded-lg border font-medium flex items-center gap-2
                        ${governance_status === 'ACTIVE'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-red-500/10 text-red-400 border-red-500/20'}`}
                    >
                        {governance_status === 'ACTIVE' ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
                        Using Model (Active)
                    </div>
                </div>
            </div>

            {/* Section 1: Safety & Stewardship KPIs */}
            <div>
                <h2 className="text-xl font-semibold text-slate-200 mb-4 flex items-center gap-2">
                    <Activity size={20} className="text-blue-400" />
                    Clinical Safety & Stewardship
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {/* NPV - The Most Critical Metric */}
                    <KPICard
                        title="NPV (Safety)"
                        value={safety.formatted_npv.value}
                        unit={safety.formatted_npv.unit}
                        status={safety.formatted_npv.status}
                        trend={safety.formatted_npv.trend}
                        icon={Shield}
                        subtext="Target: >95.0%"
                    />

                    {/* Sensitivity */}
                    <KPICard
                        title="Sensitivity"
                        value={safety.formatted_sensitivity.value}
                        unit={safety.formatted_sensitivity.unit}
                        status={safety.formatted_sensitivity.status}
                        trend={safety.formatted_sensitivity.trend}
                        icon={Activity}
                        subtext="Target: >90.0%"
                    />

                    {/* False Negatives */}
                    <KPICard
                        title="False Negatives"
                        value={safety.false_negatives_count}
                        unit="Cases"
                        status={safety.false_negatives_count > 0 ? "CRITICAL" : "OK"}
                        trend="STABLE"
                        icon={AlertTriangle}
                        subtext="Missed MRSA Cases"
                    />

                    {/* Stewardship */}
                    <KPICard
                        title="Stewardship Impact"
                        value={Math.round(stewardship.vanco_days_saved)}
                        unit="Days"
                        status="INFO"
                        trend="UP"
                        icon={Pill}
                        subtext="Est. Vanco Avoided"
                    />
                </div>
            </div>

            {/* Section 2: Hotspots & Model Health */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Ward Heatmap */}
                <div className="lg:col-span-2 bg-slate-900/50 border border-slate-800 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-slate-200 mb-4">Ward MRSA Pressure (14d)</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="text-slate-500 text-sm border-b border-slate-800">
                                    <th className="pb-3 px-2">Ward</th>
                                    <th className="pb-3 px-2">Risk Density (% RED)</th>
                                    <th className="pb-3 px-2">Trend</th>
                                    <th className="pb-3 px-2">Status</th>
                                </tr>
                            </thead>
                            <tbody className="text-slate-300">
                                {heatmap.length === 0 ? (
                                    <tr><td colSpan="4" className="p-4 text-center text-slate-500">No recent data</td></tr>
                                ) : heatmap.map((ward) => (
                                    <tr key={ward.ward} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                                        <td className="py-3 px-2 font-medium">{ward.ward}</td>
                                        <td className="py-3 px-2">
                                            <div className="flex items-center gap-2">
                                                <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
                                                    <div className={`h-full rounded-full ${ward.red_rate > 30 ? 'bg-red-500' : 'bg-emerald-500'}`} style={{ width: `${ward.red_rate}%` }}></div>
                                                </div>
                                                <span>{ward.red_rate}%</span>
                                            </div>
                                        </td>
                                        <td className="py-3 px-2 text-sm opacity-70">{ward.trend}</td>
                                        <td className="py-3 px-2">
                                            <span className={`px-2 py-1 rounded text-xs font-semibold
                                                ${ward.alert_level === 'HIGH' ? 'bg-red-500/20 text-red-400' :
                                                    ward.alert_level === 'MODERATE' ? 'bg-amber-500/20 text-amber-400' :
                                                        'bg-emerald-500/20 text-emerald-400'}`}>
                                                {ward.alert_level}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Model Health */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-slate-200 mb-4">Model Agreement</h3>
                    <div className="space-y-4">
                        {/* Consensus */}
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-slate-400">Consensus (Ensemble)</span>
                                <span className="text-emerald-400 font-medium">{(model_health.consensus_acc * 100).toFixed(1)}% Acc</span>
                            </div>
                            <div className="w-full bg-slate-800 rounded-full h-2">
                                <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${model_health.consensus_acc * 100}%` }}></div>
                            </div>
                        </div>

                        {/* RF */}
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-slate-400">Random Forest (Legacy)</span>
                                <span className="text-blue-400 font-medium">{(model_health.rf_acc * 100).toFixed(1)}% Acc</span>
                            </div>
                            <div className="w-full bg-slate-800 rounded-full h-2">
                                <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${model_health.rf_acc * 100}%` }}></div>
                            </div>
                        </div>

                        {/* XGB */}
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-slate-400">XGBoost (Challenger)</span>
                                <span className="text-purple-400 font-medium">{(model_health.xgb_acc * 100).toFixed(1)}% Acc</span>
                            </div>
                            <div className="w-full bg-slate-800 rounded-full h-2">
                                <div className="bg-purple-500 h-2 rounded-full" style={{ width: `${model_health.xgb_acc * 100}%` }}></div>
                            </div>
                        </div>

                        <div className="mt-6 p-3 bg-slate-800/50 rounded text-xs text-slate-400 leading-relaxed">
                            <strong className="text-slate-300">Governance Note:</strong> XGBoost is currently running as a "Shadow Model". Only Consensus output is shown to clinicians.
                        </div>
                    </div>
                </div>
            </div>

            {showLogModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-md p-6 shadow-2xl">
                        <h3 className="text-xl font-bold text-white mb-4">Log Governance Decision</h3>
                        <p className="text-slate-400 text-sm mb-4">Records are immutable and auditable.</p>

                        <form onSubmit={(e) => {
                            e.preventDefault();
                            // Implementation of save logic for quick prototype
                            alert("This would save the decision to DB.");
                            setShowLogModal(false);
                        }}>
                            <div className="mb-4">
                                <label className="block text-sm text-slate-400 mb-1">Action</label>
                                <select className="w-full bg-slate-800 border-slate-700 rounded p-2 text-white">
                                    <option>MONITOR (No Action)</option>
                                    <option>RETRAIN_REVIEW (Flag for ML Team)</option>
                                    <option>DISABLE_MODULE (Emergency Stop)</option>
                                </select>
                            </div>
                            <div className="mb-4">
                                <label className="block text-sm text-slate-400 mb-1">Trigger Reason</label>
                                <input className="w-full bg-slate-800 border-slate-700 rounded p-2 text-white" placeholder="e.g. NPV dropped below 95%" required />
                            </div>
                            <div className="mb-6">
                                <label className="block text-sm text-slate-400 mb-1">Notes</label>
                                <textarea className="w-full bg-slate-800 border-slate-700 rounded p-2 text-white h-24" placeholder="Justification..." required></textarea>
                            </div>

                            <div className="flex justify-end gap-3">
                                <button type="button" onClick={() => setShowLogModal(false)} className="px-4 py-2 text-slate-400 hover:text-white">Cancel</button>
                                <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium">Log Decision</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MRSAPerformanceDashboard;
