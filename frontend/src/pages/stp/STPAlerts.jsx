
import React, { useState } from 'react';
import AlertTable from '../../components/stp/AlertTable';

const STPAlerts = () => {
    const [alerts, setAlerts] = useState([]);
    const [status, setStatus] = useState('new');
    const [totalCount, setTotalCount] = useState(0);
    const [loading, setLoading] = useState(true);

    React.useEffect(() => {
        fetchAlerts();
    }, [status]);

    const fetchAlerts = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/api/stp/stage3/alerts?status=${status}`, {
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            });

            if (response.ok) {
                const data = await response.json();
                setAlerts(data.alerts || []);
                setTotalCount(data.total || 0);
            }
        } catch (error) {
            console.error("Failed to fetch alerts:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleAction = async (id, action) => {
        // Optimistic UI update
        setAlerts(prev => prev.filter(a => a.id !== id));
        setTotalCount(prev => Math.max(0, prev - 1));

        try {
            const response = await fetch(`http://localhost:8000/api/stp/stage3/alerts/${id}/status?action=${action}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                console.error("Failed to update alert status");
                fetchAlerts(); // Revert
            }
        } catch (error) {
            console.error("Error updating alert:", error);
            fetchAlerts();
        }
    };

    const tabs = [
        { id: 'new', label: 'Active' },
        { id: 'confirmed', label: 'Reviewed' },
        { id: 'dismissed', label: 'Dismissed' }
    ];

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-slate-800 dark:text-white">Alerts & Review</h2>
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-bold">
                    {status === 'new' ? `${totalCount} Pending` : `${totalCount} ${status === 'confirmed' ? 'Reviewed' : 'Dismissed'}`}
                </span>
            </div>

            <div className="flex space-x-1 border-b border-gray-200">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setStatus(tab.id)}
                        className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${status === tab.id
                                ? 'border-purple-600 text-purple-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            <AlertTable alerts={alerts} onAction={handleAction} />

            {alerts.length === 0 && (
                <div className="p-10 text-center text-slate-400 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                    {status === 'new' ? 'No active alerts. System is stable.' : 'No alerts in this category.'}
                </div>
            )}
        </div>
    );
};

export default STPAlerts;
