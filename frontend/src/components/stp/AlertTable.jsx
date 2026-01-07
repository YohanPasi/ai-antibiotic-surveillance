
import React from 'react';
import { AlertCircle, CheckCircle, Clock } from 'lucide-react';

const AlertTable = ({ alerts, onAction }) => {
    return (
        <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
            <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 font-medium border-b border-gray-200 dark:border-gray-700">
                    <tr>
                        <th className="px-4 py-3">Severity</th>
                        <th className="px-4 py-3">Alert Description</th>
                        <th className="px-4 py-3">Time</th>
                        <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-100 dark:divide-gray-800">
                    {alerts.map((alert) => (
                        <tr key={alert.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                            <td className="px-4 py-3">
                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider
                                    ${alert.severity === 'critical' ? 'bg-red-100 text-red-700' :
                                        alert.severity === 'warning' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
                                    {alert.severity === 'critical' && <AlertCircle className="w-3 h-3" />}
                                    {alert.severity}
                                </span>
                            </td>
                            <td className="px-4 py-3 text-slate-800 dark:text-gray-200 font-medium">
                                {alert.description}
                                <div className="text-xs text-slate-500 dark:text-gray-500 font-normal mt-0.5">{alert.details}</div>
                            </td>
                            <td className="px-4 py-3 text-slate-500 dark:text-gray-500 text-xs font-mono">
                                {new Date(alert.timestamp).toLocaleString()}
                            </td>
                            <td className="px-4 py-3 text-right">
                                <div className="flex justify-end gap-2">
                                    <button
                                        onClick={() => onAction(alert.id, 'dismiss')}
                                        className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                                        title="Dismiss"
                                    >
                                        <Clock className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => onAction(alert.id, 'acknowledge')}
                                        className="flex items-center gap-1 px-3 py-1.5 bg-purple-600 text-white text-xs font-bold rounded-lg hover:bg-purple-700 transition-colors shadow-sm shadow-purple-200 dark:shadow-none"
                                    >
                                        <CheckCircle className="w-3 h-3" />
                                        Review
                                    </button>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default AlertTable;
