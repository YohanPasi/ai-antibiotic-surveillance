import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, AlertTriangle, CheckCircle, TrendingUp, Clock, PlusCircle } from 'lucide-react';
import AntibiogramTable from './AntibiogramTable';
import ASTEntryForm from './ASTEntryForm';

const Dashboard = ({ setActiveView, setSelectedWard, engineVersion }) => {
    const [summary, setSummary] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isEntryOpen, setIsEntryOpen] = useState(false);

    const fetchSummary = async () => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/api/dashboard/summary`);
            const data = await response.json();
            setSummary(data.hospital_summary);
            setLoading(false);
        } catch (error) {
            console.error(error);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSummary();
    }, []);

    if (loading) return (
        <div className="flex items-center justify-center p-20 text-blue-400">
            <Clock className="animate-spin mr-3" /> Initializing Intelligent Surveillance...
        </div>
    );

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-6"
        >
            {/* Header / Actions Area */}
            <div className="flex justify-between items-end bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm transition-colors duration-300">
                <div>
                    <h2 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight">
                        Hospital Surveillance
                    </h2>
                    <p className="text-slate-500 dark:text-gray-400 mt-1 flex items-center gap-2 text-sm font-medium">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                        AI Engine Online <span className="text-slate-300 dark:text-gray-600">|</span> Mode: <span className="text-amber-500 font-bold">SHADOW VALIDATION</span>
                    </p>
                </div>

                <button
                    onClick={() => setIsEntryOpen(true)}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-semibold shadow-md shadow-blue-500/20 transition-all active:scale-95"
                >
                    <PlusCircle className="w-5 h-5" />
                    New AST Entry
                </button>
            </div>

            {/* Hospital Wide Antibiogram */}
            <AntibiogramTable />

            <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm transition-colors duration-300">
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center">
                            <Activity className="mr-3 text-blue-500" /> Ward Risk Overview
                        </h2>
                        <p className="text-slate-500 dark:text-gray-400 text-sm mt-1">Real-time Ward Ecology Monitoring</p>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="text-slate-400 dark:text-gray-500 border-b border-gray-100 dark:border-gray-700 text-xs uppercase tracking-wider">
                                <th className="p-4 font-semibold">Ward</th>
                                <th className="p-4 font-semibold">Active Alerts</th>
                                <th className="p-4 font-semibold text-center">Status Distribution</th>
                                <th className="p-4 font-semibold">Severity</th>
                                <th className="p-4 font-semibold text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {summary.map((row, idx) => (
                                <motion.tr
                                    key={idx}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ delay: idx * 0.1 }}
                                    className="border-b border-gray-50 dark:border-gray-700/50 hover:bg-slate-50 dark:hover:bg-gray-700/30 transition-colors cursor-pointer group"
                                    onClick={() => { setSelectedWard(row.ward); setActiveView('ward_detail'); }}
                                >
                                    <td className="p-4 font-bold text-slate-800 dark:text-gray-200 text-lg">{row.ward}</td>
                                    <td className="p-4 text-slate-600 dark:text-gray-300">
                                        <span className="font-mono text-xl">{row.active_alerts}</span>
                                    </td>
                                    <td className="p-4 flex space-x-2 justify-center">
                                        {row.green > 0 && <span className="bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 px-2 py-1 rounded text-xs flex items-center font-medium"><CheckCircle size={12} className="mr-1" />{row.green}</span>}
                                        {row.amber > 0 && <span className="bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800 px-2 py-1 rounded text-xs flex items-center font-medium"><TrendingUp size={12} className="mr-1" />{row.amber}</span>}
                                        {row.red > 0 && <span className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800 px-2 py-1 rounded text-xs flex items-center font-medium"><AlertTriangle size={12} className="mr-1" />{row.red}</span>}
                                    </td>
                                    <td className="p-4">
                                        <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center w-fit
                          ${row.highest_severity === 'Critical' ? 'bg-red-50 text-red-600 border border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-500/30' :
                                                row.highest_severity === 'Warning' ? 'bg-amber-50 text-amber-600 border border-amber-200 dark:bg-yellow-500/10 dark:text-yellow-300 dark:border-yellow-500/30' :
                                                    'bg-emerald-50 text-emerald-600 border border-emerald-200 dark:bg-green-500/10 dark:text-green-300 dark:border-green-500/30'}`}>
                                            {row.highest_severity.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="p-4 text-right">
                                        <span className="text-blue-600 dark:text-blue-400 text-sm font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                                            View Details →
                                        </span>
                                    </td>
                                </motion.tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* AST Entry Modal */}
            <ASTEntryForm
                isOpen={isEntryOpen}
                onClose={() => setIsEntryOpen(false)}
                onEntrySaved={fetchSummary}
            />
        </motion.div>
    );
};

export default Dashboard;
