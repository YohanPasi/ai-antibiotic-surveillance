import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, CheckCircle, AlertCircle, Clock } from 'lucide-react';

const API = 'http://localhost:8000';

const STATUS_CONFIG = {
    active: { label: 'Active', badge: 'bg-emerald-100 text-emerald-800 border-emerald-300', dot: 'bg-emerald-500' },
    shadow: { label: 'In Testing', badge: 'bg-blue-100 text-blue-800 border-blue-300', dot: 'bg-blue-500' },
    staging: { label: 'Staging', badge: 'bg-amber-100 text-amber-800 border-amber-300', dot: 'bg-amber-500' },
    archived: { label: 'Retired', badge: 'bg-gray-100 text-gray-600 border-gray-300', dot: 'bg-gray-400' },
};

const STPModelStatus = () => {
    const [data, setData] = useState({ models: [], disclaimer: '' });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${API}/api/stp/feedback/model-status`)
            .then(r => r.ok ? r.json() : { models: [] })
            .then(setData)
            .catch(() => { })
            .finally(() => setLoading(false));
    }, []);

    const getPassRateColor = (rate) => {
        if (rate >= 0.8) return { text: 'text-emerald-600', label: 'Good', bg: 'bg-emerald-500' };
        if (rate >= 0.6) return { text: 'text-amber-600', label: 'Fair', bg: 'bg-amber-500' };
        return { text: 'text-red-600', label: 'Needs Attention', bg: 'bg-red-500' };
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Surveillance System Health</h1>
                <p className="text-sm text-slate-500 mt-0.5">Status and accuracy of the detection system running in the background</p>
            </div>

            {/* Notice */}
            <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 flex gap-3">
                <Activity className="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-purple-800 leading-relaxed">
                    This page shows how well the surveillance system is performing. A higher accuracy means the system's predictions have been matching real lab results closely.
                </p>
            </div>

            {loading ? (
                <div className="flex items-center justify-center h-48">
                    <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
                </div>
            ) : data.models.length === 0 ? (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 py-16 text-center">
                    <Clock className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                    <p className="font-semibold text-slate-500">No system records found</p>
                    <p className="text-sm text-slate-400 mt-1">The surveillance system hasn't been initialised yet</p>
                </div>
            ) : (
                <div className="grid gap-5">
                    {data.models.map(model => {
                        const cfg = STATUS_CONFIG[model.status] || STATUS_CONFIG.active;
                        const passRate = getPassRateColor(model.pass_rate);
                        const passPercent = Math.round(model.pass_rate * 100);
                        const errorPercent = (model.avg_error * 100).toFixed(1);
                        const isUnderperforming = model.pass_rate < 0.7 && model.validations > 0;

                        return (
                            <div key={model.model_id} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm hover:shadow-md transition-shadow overflow-hidden">
                                {/* Card header */}
                                <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between gap-3">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-3 h-3 rounded-full ${cfg.dot} flex-shrink-0`} />
                                        <div>
                                            <h3 className="font-semibold text-slate-800 dark:text-white capitalize">{model.type || 'Surveillance Engine'}</h3>
                                            <p className="text-xs text-slate-500 mt-0.5">Detection system</p>
                                        </div>
                                    </div>
                                    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${cfg.badge}`}>
                                        {cfg.label}
                                    </span>
                                </div>

                                {/* Metrics */}
                                <div className="px-6 py-5">
                                    <div className="grid grid-cols-3 gap-6">
                                        {/* Checks done */}
                                        <div className="flex items-start gap-3">
                                            <div className="p-2 bg-blue-50 rounded-lg flex-shrink-0">
                                                <TrendingUp className="w-5 h-5 text-blue-600" />
                                            </div>
                                            <div>
                                                <div className="text-2xl font-black text-slate-800 dark:text-white">{model.validations}</div>
                                                <div className="text-xs text-slate-500">Checks Completed</div>
                                            </div>
                                        </div>

                                        {/* Accuracy */}
                                        <div className="flex items-start gap-3">
                                            <div className="p-2 bg-emerald-50 rounded-lg flex-shrink-0">
                                                <CheckCircle className="w-5 h-5 text-emerald-600" />
                                            </div>
                                            <div>
                                                <div className={`text-2xl font-black ${passRate.text}`}>{passPercent}%</div>
                                                <div className="text-xs text-slate-500">Prediction Accuracy</div>
                                            </div>
                                        </div>

                                        {/* Avg Error */}
                                        <div className="flex items-start gap-3">
                                            <div className="p-2 bg-amber-50 rounded-lg flex-shrink-0">
                                                <AlertCircle className="w-5 h-5 text-amber-600" />
                                            </div>
                                            <div>
                                                <div className="text-2xl font-black text-slate-800 dark:text-white">{errorPercent}%</div>
                                                <div className="text-xs text-slate-500">Average Deviation</div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Accuracy bar */}
                                    {model.validations > 0 && (
                                        <div className="mt-5">
                                            <div className="flex items-center justify-between mb-1.5">
                                                <span className="text-xs text-slate-500">Accuracy</span>
                                                <span className={`text-xs font-bold ${passRate.text}`}>{passRate.label}</span>
                                            </div>
                                            <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                                                <div className={`h-full rounded-full transition-all ${passRate.bg}`} style={{ width: `${passPercent}%` }} />
                                            </div>
                                        </div>
                                    )}

                                    {/* Alert for underperforming */}
                                    {isUnderperforming && (
                                        <div className="mt-4 flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2.5 text-sm text-amber-800">
                                            <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                                            <span>The system's accuracy is lower than expected. Your system administrator has been notified.</span>
                                        </div>
                                    )}
                                    {!isUnderperforming && model.validations > 0 && model.pass_rate >= 0.8 && (
                                        <div className="mt-4 flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2.5 text-sm text-emerald-800">
                                            <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                                            <span>System is performing well and predictions are reliable.</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default STPModelStatus;
