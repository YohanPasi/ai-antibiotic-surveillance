
import React, { useState, useEffect } from 'react';
import { Activity, Shield, Users, TrendingUp } from 'lucide-react';
import ModelStatusBadge from '../../components/stp/ModelStatusBadge';

const STPOverview = () => {
    const [stats, setStats] = useState({
        activeAlerts: 0,
        psiScore: 0.0,
        modelMode: 'INITIALIZING',
        lastInference: null,
        activeAlerts: 0,
        psiScore: 0.0,
        modelMode: 'INITIALIZING',
        lastInference: null,
        monitoredWards: 0,
        logs: [],
        trends: []
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/stp/overview/stats');
                if (response.ok) {
                    const data = await response.json();

                    // Fetch Logs
                    const logsRes = await fetch('http://localhost:8000/api/stp/overview/logs');
                    const logsData = logsRes.ok ? await logsRes.json() : { logs: [] };

                    // Fetch Trends
                    const trendsRes = await fetch('http://localhost:8000/api/stp/overview/trends_preview');
                    const trendsData = trendsRes.ok ? await trendsRes.json() : { trends: [] };

                    setStats({ ...data, logs: logsData.logs, trends: trendsData.trends });
                }
            } catch (error) {
                console.error("Failed to load overview stats", error);
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800 dark:text-white">STP Surveillance Overview</h2>
                    <p className="text-sm text-slate-500">Streptococcus & Enterococcus Monitoring</p>
                </div>
                <ModelStatusBadge mode={stats.modelMode} />
            </div>

            {/* Disclaimer Banner */}
            <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-lg">
                <div className="flex gap-3">
                    <Shield className="w-5 h-5 text-amber-500" />
                    <p className="text-sm text-amber-800 font-medium">
                        ⚠ Surveillance System Only – Not for clinical decision-making. (M70 Policy Enforced)
                    </p>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">Active Alerts</p>
                            <h3 className="text-3xl font-bold text-slate-800 dark:text-gray-100 mt-2">{stats.activeAlerts}</h3>
                        </div>
                        <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg text-purple-600 dark:text-purple-400">
                            <Activity className="w-5 h-5" />
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">Drift (PSI)</p>
                            <h3 className="text-3xl font-bold text-slate-800 dark:text-gray-100 mt-2">{stats.psiScore}</h3>
                        </div>
                        <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg text-blue-600 dark:text-blue-400">
                            <TrendingUp className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-xs text-green-600 mt-2 font-medium">Stable (Below 0.1)</p>
                </div>

                <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">Monitored Wards</p>
                            <h3 className="text-3xl font-bold text-slate-800 dark:text-gray-100 mt-2">{stats.monitoredWards}</h3>
                        </div>
                        <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg text-green-600 dark:text-green-400">
                            <Users className="w-5 h-5" />
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">Last Update</p>
                            <h3 className="text-lg font-bold text-slate-800 dark:text-gray-100 mt-2">
                                {stats.lastInference ? new Date(stats.lastInference).toLocaleDateString() : 'Pending'}
                            </h3>
                        </div>
                        <div className="p-2 bg-gray-100 dark:bg-gray-700/50 rounded-lg text-gray-500">
                            <Activity className="w-5 h-5" />
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Placeholder for Quick Actions or recent activity */}
                {/* Emerging Trends (Replacing Map View) */}
                <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm min-h-[300px]">
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4">Emerging Resistance Trends</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-slate-500 uppercase bg-gray-50 dark:bg-gray-700">
                                <tr>
                                    <th className="px-3 py-2">Ward</th>
                                    <th className="px-3 py-2">Organism</th>
                                    <th className="px-3 py-2">Trend</th>
                                </tr>
                            </thead>
                            <tbody>
                                {stats.trends && stats.trends.length > 0 ? (
                                    stats.trends.map((t, i) => (
                                        <tr key={i} className="border-b dark:border-gray-700">
                                            <td className="px-3 py-2 font-medium">{t.ward}</td>
                                            <td className="px-3 py-2">
                                                <div className="font-bold">{t.organism}</div>
                                                <div className="text-xs text-slate-400">{t.antibiotic}</div>
                                            </td>
                                            <td className="px-3 py-2">
                                                <span className={`px-2 py-1 rounded text-xs font-bold ${t.trend === 'increasing' ? 'text-red-600 bg-red-100' : 'text-green-600 bg-green-100'}`}>
                                                    {t.trend === 'increasing' ? '▲' : '▼'} {(t.slope * 100).toFixed(2)}%
                                                </span>
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="3" className="px-3 py-4 text-center text-slate-400">No significant trends detected.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Recent System Logs */}
                <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm min-h-[300px]">
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4">Recent System Logs</h3>
                    <div className="space-y-3">
                        {stats.logs && stats.logs.length > 0 ? (
                            stats.logs.map((log, idx) => (
                                <div key={idx} className="flex gap-3 text-sm border-b border-gray-100 dark:border-gray-700 pb-2 last:border-0">
                                    <div className={`mt-1 min-w-[8px] h-2 rounded-full ${log.type === 'high' ? 'bg-red-500' :
                                            log.type === 'medium' ? 'bg-amber-500' : 'bg-blue-500'
                                        }`} />
                                    <div>
                                        <p className="text-slate-800 dark:text-slate-200 font-medium">{log.message}</p>
                                        <p className="text-xs text-slate-400">{log.date}</p>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-center text-slate-400 py-10">No recent logs available.</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default STPOverview;
