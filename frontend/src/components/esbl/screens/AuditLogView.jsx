import React, { useEffect, useState } from 'react';
import { esblService } from '../../../services/esblService';

export const AuditLogView = ({ onClose }) => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadLogs();
    }, []);

    const loadLogs = async () => {
        try {
            const data = await esblService.getAuditLogs();
            setLogs(data || []);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    // Derived Stats
    const totalCases = logs.length;
    const overrides = logs.filter(l => l.decision === 'OVERRIDE').length;
    const complianceRate = totalCases > 0 ? ((1 - (overrides / totalCases)) * 100).toFixed(1) : 100;

    return (
        <div className="bg-white rounded-2xl w-full h-full flex flex-col shadow-sm border border-slate-200 animate-fadeIn">

            {/* Header */}
            <div className="bg-slate-50 border-b border-slate-200 p-6 flex justify-between items-center">
                <div>
                    <h2 className="text-xl font-bold text-slate-900">Governance Audit Trail</h2>
                    <div className="flex gap-4 mt-2 text-sm">
                        <span className="text-slate-500">Total Records: <strong className="text-slate-800">{totalCases}</strong></span>
                        <span className="text-slate-500">Override Rate: <strong className="text-slate-800">{overrides > 0 ? (overrides / totalCases * 100).toFixed(1) : 0}%</strong></span>
                        <span className="text-slate-500">Compliance: <strong className="text-green-700">{complianceRate}%</strong></span>
                    </div>
                </div>
                {onClose && (
                    <button onClick={onClose} className="p-2 hover:bg-slate-200 rounded-full transition-colors">
                        <svg className="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                )}
            </div>

            {/* Table */}
            <div className="flex-1 overflow-auto p-0 scrollbar-thin scrollbar-thumb-slate-200">
                <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 text-slate-500 font-medium border-b sticky top-0 z-10">
                        <tr>
                            <th className="p-4 bg-slate-50">Timestamp</th>
                            <th className="p-4 bg-slate-50">Encounter ID</th>
                            <th className="p-4 bg-slate-50">Decision</th>
                            <th className="p-4 bg-slate-50">Reason Code</th>
                            <th className="p-4 bg-slate-50">Model Ver</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {loading ? (
                            <tr><td colSpan="5" className="p-8 text-center text-slate-400">Loading audit trail...</td></tr>
                        ) : logs.length === 0 ? (
                            <tr><td colSpan="5" className="p-8 text-center text-slate-400">No audit records found.</td></tr>
                        ) : (
                            logs.map((log, i) => (
                                <tr key={i} className="hover:bg-slate-50 transition-colors">
                                    <td className="p-4 text-slate-500 font-mono text-xs">{new Date(log.timestamp).toLocaleString()}</td>
                                    <td className="p-4 font-mono text-xs text-slate-400">{log.encounter_id?.substring(0, 8)}</td>
                                    <td className="p-4">
                                        <span className={`px-2 py-1 rounded text-xs font-bold ${log.decision === 'OVERRIDE'
                                                ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                                : 'bg-green-100 text-green-800 border border-green-200'
                                            }`}>
                                            {log.decision}
                                        </span>
                                    </td>
                                    <td className="p-4 font-medium text-slate-700">{log.reason_code || "-"}</td>
                                    <td className="p-4 text-xs text-slate-400 font-mono">{log.model_version}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <div className="p-4 border-t bg-slate-50 text-xs text-center text-slate-400">
                Automated Governance Logger v1.0 • Immutable Record
            </div>
        </div>
    );
};
