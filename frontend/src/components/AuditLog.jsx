import React, { useState, useEffect } from 'react';

const AuditLog = () => {
    const [logs, setLogs] = useState([]);

    useEffect(() => {
        fetch('http://localhost:8000/api/audit/logs')
            .then(res => res.json())
            .then(data => setLogs(data.logs))
            .catch(err => console.error(err));
    }, []);

    return (
        <div className="bg-gray-900 p-6 rounded-lg border border-gray-800 mt-8">
            <h3 className="text-xl font-bold text-gray-300 mb-4 flex items-center">
                <span className="text-2xl mr-2">🛡️</span> Defense Audit Log (Traceability)
            </h3>
            <div className="overflow-x-auto max-h-96">
                <table className="w-full text-left text-xs font-mono text-gray-400">
                    <thead className="bg-gray-800 sticky top-0">
                        <tr>
                            <th className="p-2">Timestamp</th>
                            <th className="p-2">Target</th>
                            <th className="p-2">Status</th>
                            <th className="p-2">Deviation</th>
                            <th className="p-2">Reason</th>
                            <th className="p-2">Model Ver</th>
                        </tr>
                    </thead>
                    <tbody>
                        {logs.map((log, idx) => (
                            <tr key={idx} className="border-b border-gray-800 hover:bg-gray-800">
                                <td className="p-2">{new Date(log.timestamp).toISOString().split('T')[0]}</td>
                                <td className="p-2">{log.ward} | {log.organism.substring(0, 15)}... | {log.antibiotic.substring(0, 5)}...</td>
                                <td className="p-2 uppercase font-bold text-white">{log.status}</td>
                                <td className="p-2 text-white">{log.deviation.toFixed(2)}</td>
                                <td className="p-2 text-gray-300">{log.reason}</td>
                                <td className="p-2 text-gray-500">{log.model_version}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AuditLog;
