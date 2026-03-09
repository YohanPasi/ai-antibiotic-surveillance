import React, { useState, useEffect } from 'react';
import { Activity, AlertTriangle, Building2, Clock, TrendingUp, TrendingDown, ShieldAlert, CheckCircle } from 'lucide-react';

const API = 'http://localhost:8000';

const STPOverview = () => {
    const [stats, setStats] = useState(null);
    const [logs, setLogs] = useState([]);
    const [trends, setTrends] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAll = async () => {
            try {
                const [statsRes, logsRes, trendsRes] = await Promise.all([
                    fetch(`${API}/api/stp/overview/stats`),
                    fetch(`${API}/api/stp/overview/logs`),
                    fetch(`${API}/api/stp/overview/trends_preview`)
                ]);
                if (statsRes.ok) setStats(await statsRes.json());
                if (logsRes.ok) { const d = await logsRes.json(); setLogs(d.logs || []); }
                if (trendsRes.ok) { const d = await trendsRes.json(); setTrends(d.trends || []); }
            } catch (e) {
                console.error('Failed to load overview', e);
            } finally {
                setLoading(false);
            }
        };
        fetchAll();
    }, []);

    const formatDate = (iso) => {
        if (!iso) return 'Not available';
        try { return new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
        catch { return iso; }
    };

    const getModelLabel = (mode) => {
        const map = { active: 'Running Normally', calibrating: 'Calibrating', training: 'Updating', initializing: 'Starting Up' };
        return map[mode?.toLowerCase()] || 'Running';
    };
    const getModelColor = (mode) => {
        const map = { active: 'text-emerald-600 bg-emerald-50 border-emerald-200', calibrating: 'text-amber-600 bg-amber-50 border-amber-200', training: 'text-blue-600 bg-blue-50 border-blue-200', initializing: 'text-gray-600 bg-gray-50 border-gray-200' };
        return map[mode?.toLowerCase()] || 'text-emerald-600 bg-emerald-50 border-emerald-200';
    };

    const getSeverityStyle = (type) => {
        if (type === 'high' || type === 'critical') return 'bg-red-100 text-red-700 border-l-red-500';
        if (type === 'medium' || type === 'warning') return 'bg-amber-100 text-amber-700 border-l-amber-500';
        return 'bg-blue-50 text-blue-700 border-l-blue-400';
    };
    const getSeverityIcon = (type) => {
        if (type === 'high' || type === 'critical') return <ShieldAlert className="w-4 h-4 text-red-500 flex-shrink-0" />;
        if (type === 'medium' || type === 'warning') return <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0" />;
        return <CheckCircle className="w-4 h-4 text-blue-500 flex-shrink-0" />;
    };

    if (loading) return (
        <div className="flex items-center justify-center h-64">
            <div className="text-center">
                <div className="w-10 h-10 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <p className="text-slate-500 font-medium">Loading surveillance data…</p>
            </div>
        </div>
    );

    return (
        <div className="space-y-6">
            {/* Page Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 dark:text-white">STP Surveillance Overview</h1>
                    <p className="text-sm text-slate-500 mt-0.5">Streptococcus &amp; Enterococcus · Hospital-wide resistance monitoring</p>
                </div>
                {stats && (
                    <span className={`self-start sm:self-auto px-4 py-1.5 rounded-full text-xs font-semibold border ${getModelColor(stats.modelMode)}`}>
                        ● System {getModelLabel(stats.modelMode)}
                    </span>
                )}
            </div>

            {/* Surveillance Notice */}
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-3">
                <ShieldAlert className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-amber-800 leading-relaxed">
                    <strong>For surveillance purposes only.</strong> This information is intended to support infection prevention planning and epidemiological monitoring.
                    It must <strong>not</strong> be used to make individual patient treatment decisions.
                </p>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <KpiCard
                    icon={<AlertTriangle className="w-6 h-6 text-red-500" />}
                    bg="bg-red-50"
                    label="Active Alerts"
                    value={stats?.activeAlerts ?? 0}
                    sub="Require review"
                    highlight={stats?.activeAlerts > 0}
                />
                <KpiCard
                    icon={<Building2 className="w-6 h-6 text-purple-500" />}
                    bg="bg-purple-50"
                    label="Wards Monitored"
                    value={stats?.monitoredWards ?? 0}
                    sub="Hospital units"
                />
                <KpiCard
                    icon={<Activity className="w-6 h-6 text-blue-500" />}
                    bg="bg-blue-50"
                    label="System Status"
                    value={getModelLabel(stats?.modelMode)}
                    valueSm
                    sub="Surveillance engine"
                />
                <KpiCard
                    icon={<Clock className="w-6 h-6 text-emerald-500" />}
                    bg="bg-emerald-50"
                    label="Last Updated"
                    value={stats?.lastInference ? formatDate(stats.lastInference).split(',')[0] : '—'}
                    valueSm
                    sub={stats?.lastInference ? formatDate(stats.lastInference).split(',').slice(1).join(',').trim() : 'No data yet'}
                />
            </div>

            {/* Main content grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Emerging Resistance Trends */}
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                    <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
                        <h2 className="font-semibold text-slate-800 dark:text-white">Emerging Resistance Patterns</h2>
                        <p className="text-xs text-slate-500 mt-0.5">Wards showing notable changes in resistance levels</p>
                    </div>
                    <div className="divide-y divide-gray-50 dark:divide-gray-700">
                        {trends.length === 0 ? (
                            <div className="px-6 py-10 text-center text-slate-400 text-sm">No significant changes detected</div>
                        ) : trends.map((t, i) => (
                            <div key={i} className="px-6 py-3 flex items-center justify-between gap-4 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
                                <div className="min-w-0">
                                    <p className="font-medium text-sm text-slate-800 dark:text-gray-100 truncate">{t.organism}</p>
                                    <p className="text-xs text-slate-500 mt-0.5">{t.ward} · {t.antibiotic}</p>
                                </div>
                                <div className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold flex-shrink-0 ${t.trend === 'increasing' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                                    {t.trend === 'increasing'
                                        ? <TrendingUp className="w-3.5 h-3.5" />
                                        : <TrendingDown className="w-3.5 h-3.5" />}
                                    {t.trend === 'increasing' ? 'Rising' : 'Falling'}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Recent Activity */}
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                    <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
                        <h2 className="font-semibold text-slate-800 dark:text-white">Recent Activity</h2>
                        <p className="text-xs text-slate-500 mt-0.5">Latest surveillance events and notifications</p>
                    </div>
                    <div className="divide-y divide-gray-50 dark:divide-gray-700">
                        {logs.length === 0 ? (
                            <div className="px-6 py-10 text-center text-slate-400 text-sm">No recent activity</div>
                        ) : logs.map((log, i) => (
                            <div key={i} className={`mx-4 my-2 px-4 py-3 rounded-lg border-l-4 flex items-start gap-3 ${getSeverityStyle(log.type)}`}>
                                {getSeverityIcon(log.type)}
                                <div className="min-w-0">
                                    <p className="text-sm font-medium leading-snug">{log.message}</p>
                                    <p className="text-xs opacity-70 mt-0.5">{log.date}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

const KpiCard = ({ icon, bg, label, value, sub, highlight = false, valueSm = false }) => (
    <div className={`bg-white dark:bg-gray-800 rounded-xl border shadow-sm p-5 flex items-start gap-4 ${highlight ? 'border-red-200' : 'border-gray-100 dark:border-gray-700'}`}>
        <div className={`${bg} p-3 rounded-xl flex-shrink-0`}>{icon}</div>
        <div className="min-w-0">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
            <p className={`font-bold text-slate-800 dark:text-white mt-0.5 leading-tight ${valueSm ? 'text-lg' : 'text-2xl'} ${highlight ? 'text-red-600' : ''}`}>{value}</p>
            <p className="text-xs text-slate-400 mt-0.5">{sub}</p>
        </div>
    </div>
);

export default STPOverview;
