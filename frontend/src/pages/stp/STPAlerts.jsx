import React, { useState } from 'react';
import { CheckCircle, XCircle, AlertTriangle, ShieldAlert, BellRing, Clock } from 'lucide-react';

const API = 'http://localhost:8000';

const SEVERITY_CONFIG = {
    critical: { label: 'High Priority', dot: 'bg-red-500', badge: 'bg-red-100 text-red-700 border-red-200', ring: 'border-l-red-500', icon: <ShieldAlert className="w-4 h-4 text-red-500" /> },
    high: { label: 'High Priority', dot: 'bg-red-500', badge: 'bg-red-100 text-red-700 border-red-200', ring: 'border-l-red-500', icon: <ShieldAlert className="w-4 h-4 text-red-500" /> },
    medium: { label: 'Medium Priority', dot: 'bg-amber-400', badge: 'bg-amber-100 text-amber-700 border-amber-200', ring: 'border-l-amber-400', icon: <AlertTriangle className="w-4 h-4 text-amber-500" /> },
    low: { label: 'Low Priority', dot: 'bg-blue-400', badge: 'bg-blue-100 text-blue-700 border-blue-200', ring: 'border-l-blue-400', icon: <BellRing className="w-4 h-4 text-blue-500" /> },
};

const STPAlerts = () => {
    const [alerts, setAlerts] = useState([]);
    const [status, setStatus] = useState('new');
    const [totalCount, setTotalCount] = useState(0);
    const [loading, setLoading] = useState(true);

    React.useEffect(() => { fetchAlerts(); }, [status]);

    const fetchAlerts = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/stp/stage3/alerts?status=${status}`, {
                headers: { 'Cache-Control': 'no-cache' }
            });
            if (res.ok) {
                const data = await res.json();
                setAlerts(data.alerts || []);
                setTotalCount(data.total || 0);
            }
        } catch (e) {
            console.error('Failed to fetch alerts:', e);
        } finally {
            setLoading(false);
        }
    };

    const handleAction = async (id, action) => {
        setAlerts(prev => prev.filter(a => a.id !== id));
        setTotalCount(prev => Math.max(0, prev - 1));
        try {
            const res = await fetch(`${API}/api/stp/stage3/alerts/${id}/status?action=${action}`, { method: 'PATCH' });
            if (!res.ok) fetchAlerts();
        } catch { fetchAlerts(); }
    };

    const formatDate = (iso) => {
        try { return new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
        catch { return iso || '—'; }
    };

    const tabs = [
        { id: 'new', label: 'Pending Review', emptyMsg: 'All clear — no alerts waiting for review.' },
        { id: 'confirmed', label: 'Acknowledged', emptyMsg: 'No acknowledged alerts.' },
        { id: 'dismissed', label: 'Dismissed', emptyMsg: 'No dismissed alerts.' },
    ];

    const activeTab = tabs.find(t => t.id === status);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Resistance Alerts</h1>
                    <p className="text-sm text-slate-500 mt-0.5">Review and manage surveillance alerts raised by the system</p>
                </div>
                {status === 'new' && totalCount > 0 && (
                    <span className="self-start sm:self-auto px-3 py-1.5 bg-red-500 text-white rounded-full text-sm font-bold animate-pulse">
                        {totalCount} Pending
                    </span>
                )}
            </div>

            {/* Tabs */}
            <div className="bg-gray-100 dark:bg-gray-800 rounded-xl p-1 flex gap-1">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setStatus(tab.id)}
                        className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-semibold transition-all duration-200 ${status === tab.id
                            ? 'bg-white dark:bg-gray-700 text-purple-700 dark:text-purple-300 shadow-sm'
                            : 'text-slate-500 hover:text-slate-700 dark:hover:text-gray-300'}`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Alerts List */}
            {loading ? (
                <div className="flex items-center justify-center h-40">
                    <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
                </div>
            ) : alerts.length === 0 ? (
                <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-12 text-center">
                    <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                    <p className="font-semibold text-slate-600 dark:text-gray-300">{activeTab?.emptyMsg}</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {alerts.map(alert => {
                        const cfg = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.low;
                        return (
                            <div key={alert.id} className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 border-l-4 ${cfg.ring} shadow-sm hover:shadow-md transition-shadow`}>
                                <div className="p-5">
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="flex items-start gap-3 min-w-0">
                                            <div className="mt-0.5">{cfg.icon}</div>
                                            <div className="min-w-0">
                                                <div className="flex flex-wrap items-center gap-2 mb-1">
                                                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${cfg.badge}`}>
                                                        {cfg.label}
                                                    </span>
                                                </div>
                                                <h3 className="font-semibold text-slate-800 dark:text-white text-sm leading-snug">{alert.description}</h3>
                                                <p className="text-xs text-slate-500 mt-1">{alert.details}</p>
                                                <div className="flex items-center gap-1.5 mt-2 text-xs text-slate-400">
                                                    <Clock className="w-3.5 h-3.5" />
                                                    <span>Detected: {formatDate(alert.timestamp)}</span>
                                                </div>
                                            </div>
                                        </div>

                                        {status === 'new' && (
                                            <div className="flex gap-2 flex-shrink-0">
                                                <button
                                                    onClick={() => handleAction(alert.id, 'acknowledge')}
                                                    className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg text-xs font-semibold hover:bg-emerald-100 transition-colors"
                                                >
                                                    <CheckCircle className="w-3.5 h-3.5" /> Acknowledge
                                                </button>
                                                <button
                                                    onClick={() => handleAction(alert.id, 'dismiss')}
                                                    className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-50 text-gray-600 border border-gray-200 rounded-lg text-xs font-semibold hover:bg-gray-100 transition-colors"
                                                >
                                                    <XCircle className="w-3.5 h-3.5" /> Dismiss
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default STPAlerts;
