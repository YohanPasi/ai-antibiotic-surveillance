
import React from 'react';
import { ShieldAlert, AlertTriangle, BellRing, CheckCircle, X } from 'lucide-react';

const SEVERITY_MAP = {
    critical: { label: 'High Priority', cls: 'bg-red-100 text-red-700', icon: <ShieldAlert className="w-3 h-3" /> },
    high: { label: 'High Priority', cls: 'bg-red-100 text-red-700', icon: <ShieldAlert className="w-3 h-3" /> },
    medium: { label: 'Moderate', cls: 'bg-amber-100 text-amber-700', icon: <AlertTriangle className="w-3 h-3" /> },
    warning: { label: 'Moderate', cls: 'bg-amber-100 text-amber-700', icon: <AlertTriangle className="w-3 h-3" /> },
    low: { label: 'Low', cls: 'bg-blue-100 text-blue-700', icon: <BellRing className="w-3 h-3" /> },
};

const formatDate = (iso) => {
    try { return new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return iso; }
};

const AlertTable = ({ alerts = [], onAction }) => {
    if (!alerts.length) return null;

    return (
        <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
            <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 dark:bg-gray-800 text-xs text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wide border-b border-gray-200 dark:border-gray-700">
                    <tr>
                        <th className="px-4 py-3">Priority</th>
                        <th className="px-4 py-3">Alert</th>
                        <th className="px-4 py-3">Detected</th>
                        <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-100 dark:divide-gray-800">
                    {alerts.map(alert => {
                        const cfg = SEVERITY_MAP[alert.severity] || SEVERITY_MAP.low;
                        return (
                            <tr key={alert.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                                <td className="px-4 py-3.5">
                                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${cfg.cls}`}>
                                        {cfg.icon} {cfg.label}
                                    </span>
                                </td>
                                <td className="px-4 py-3.5">
                                    <p className="font-semibold text-slate-800 dark:text-gray-100">{alert.description}</p>
                                    <p className="text-xs text-slate-500 mt-0.5">{alert.details}</p>
                                </td>
                                <td className="px-4 py-3.5 text-xs text-slate-500 dark:text-gray-400 whitespace-nowrap">
                                    {formatDate(alert.timestamp)}
                                </td>
                                <td className="px-4 py-3.5 text-right">
                                    <div className="flex justify-end gap-2">
                                        <button
                                            onClick={() => onAction(alert.id, 'dismiss')}
                                            className="flex items-center gap-1 px-2.5 py-1.5 text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                                        >
                                            <X className="w-3.5 h-3.5" /> Dismiss
                                        </button>
                                        <button
                                            onClick={() => onAction(alert.id, 'acknowledge')}
                                            className="flex items-center gap-1 px-3 py-1.5 bg-purple-600 text-white text-xs font-semibold rounded-lg hover:bg-purple-700 transition-colors"
                                        >
                                            <CheckCircle className="w-3.5 h-3.5" /> Acknowledge
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};

export default AlertTable;
