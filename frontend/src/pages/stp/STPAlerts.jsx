
import React, { useState } from 'react';
import AlertTable from '../../components/stp/AlertTable';

const STPAlerts = () => {
    const [alerts, setAlerts] = useState([
        { id: '1', severity: 'critical', description: 'High Risk Spike in ICU', details: 'E. coli resistance > 30%', timestamp: new Date().toISOString() },
        { id: '2', severity: 'warning', description: 'Drift Detected', details: 'Feature PSI > 0.15', timestamp: new Date(Date.now() - 3600000).toISOString() },
    ]);

    const handleAction = (id, action) => {
        alert(`${action} alert ${id}`);
        // In real app: API call
        if (action === 'dismiss' || action === 'acknowledge') {
            setAlerts(prev => prev.filter(a => a.id !== id));
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-slate-800 dark:text-white">Active Alerts & Review</h2>
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-bold">{alerts.length} Pending</span>
            </div>

            <AlertTable alerts={alerts} onAction={handleAction} />

            {alerts.length === 0 && (
                <div className="p-10 text-center text-slate-400 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                    No active alerts. System is stable.
                </div>
            )}
        </div>
    );
};

export default STPAlerts;
