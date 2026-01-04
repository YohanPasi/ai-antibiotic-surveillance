import React, { useState, useEffect } from 'react';

const MRSAValidationLog = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchLogs();
    }, []);

    const fetchLogs = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('http://localhost:8000/api/mrsa/validation-logs', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setLogs(data);
            }
        } catch (error) {
            console.error("Failed to fetch validation logs", error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-4 text-slate-400">Loading Validation History...</div>;

    return (
        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-6 overflow-hidden">
            <h3 className="text-xl font-bold text-slate-200 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                Prediction Validation History (Stage D)
            </h3>

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="text-xs uppercase text-slate-500 border-b border-white/10">
                            <th className="p-3">Date</th>
                            <th className="p-3">Ward</th>
                            <th className="p-3">Sample</th>
                            <th className="p-3">Prediction</th>
                            <th className="p-3">Actual (FOX)</th>
                            <th className="p-3">Outcome</th>
                        </tr>
                    </thead>
                    <tbody className="text-sm">
                        {logs.length === 0 ? (
                            <tr>
                                <td colSpan="6" className="p-4 text-center text-slate-500">No validation records found yet.</td>
                            </tr>
                        ) : (
                            logs.map((log) => (
                                <tr key={log.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                    <td className="p-3 text-slate-300">{new Date(log.validation_date).toLocaleDateString()}</td>
                                    <td className="p-3 text-slate-400">{log.ward}</td>
                                    <td className="p-3 text-slate-400">{log.sample_type}</td>
                                    <td className="p-3">
                                        <span className={`px-2 py-1 rounded text-xs font-bold ${log.consensus_band === 'RED' ? 'bg-red-500/20 text-red-400' :
                                                log.consensus_band === 'AMBER' ? 'bg-amber-500/20 text-amber-400' :
                                                    'bg-emerald-500/20 text-emerald-400'
                                            }`}>
                                            {log.consensus_band}
                                        </span>
                                    </td>
                                    <td className="p-3 text-slate-300 font-mono">
                                        {log.cefoxitin_result} ({log.actual_mrsa ? 'MRSA' : 'MSSA'})
                                    </td>
                                    <td className="p-3">
                                        {log.consensus_correct ? (
                                            <span className="flex items-center gap-1 text-emerald-400 font-bold">
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
                                                Correct
                                            </span>
                                        ) : (
                                            <span className="flex items-center gap-1 text-red-400 font-bold">
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                                                Missed
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default MRSAValidationLog;
