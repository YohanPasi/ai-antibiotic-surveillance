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
            <div className="flex justify-between items-end bg-gray-900/50 p-4 rounded-lg border border-gray-800 backdrop-blur-sm">
                <div>
                    <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                        Hospital Surveillance Command
                    </h2>
                    <p className="text-gray-400 mt-1 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                        AI Engine Online | Mode: <span className="text-yellow-500 font-bold">SHADOW VALIDATION</span>
                    </p>
                </div>

                <button
                    onClick={() => setIsEntryOpen(true)}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-lg font-bold shadow-lg shadow-blue-900/20 transition-all border border-blue-500 hover:scale-105 active:scale-95"
                >
                    <PlusCircle className="w-5 h-5" />
                    New AST Entry
                </button>
            </div>

            {/* Hospital Wide Antibiogram */}
            <AntibiogramTable />

            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-xl">
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-white flex items-center">
                            <Activity className="mr-3 text-blue-400" /> Ward Risk Overview
                        </h2>
                        <p className="text-gray-400 text-sm mt-1">Real-time Ward Ecology Monitoring</p>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="text-gray-400 border-b border-gray-700">
                                <th className="p-4 font-semibold">Ward</th>
                                <th className="p-4 font-semibold">Active Alerts</th>
                                <th className="p-4 font-semibold text-center">Status Distribution</th>
                                <th className="p-4 font-semibold">Severity</th>
                                <th className="p-4 font-semibold">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {summary.map((row, idx) => (
                                <motion.tr
                                    key={idx}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ delay: idx * 0.1 }}
                                    className="border-b border-gray-700 hover:bg-gray-700/50 transition cursor-pointer"
                                    onClick={() => { setSelectedWard(row.ward); setActiveView('ward_detail'); }}
                                >
                                    <td className="p-4 font-bold text-white text-lg">{row.ward}</td>
                                    <td className="p-4 text-white">
                                        <span className="font-mono text-xl">{row.active_alerts}</span>
                                    </td>
                                    <td className="p-4 flex space-x-2 justify-center">
                                        {row.green > 0 && <span className="bg-green-900/50 text-green-400 border border-green-700 px-2 py-1 rounded text-xs flex items-center"><CheckCircle size={12} className="mr-1" />{row.green}</span>}
                                        {row.amber > 0 && <span className="bg-yellow-900/50 text-yellow-400 border border-yellow-700 px-2 py-1 rounded text-xs flex items-center"><TrendingUp size={12} className="mr-1" />{row.amber}</span>}
                                        {row.red > 0 && <span className="bg-red-900/50 text-red-400 border border-red-700 px-2 py-1 rounded text-xs flex items-center"><AlertTriangle size={12} className="mr-1" />{row.red}</span>}
                                    </td>
                                    <td className="p-4">
                                        <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center w-fit
                          ${row.highest_severity === 'Critical' ? 'bg-red-500/20 text-red-300 border border-red-500' :
                                                row.highest_severity === 'Warning' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500' : 'bg-green-500/20 text-green-300 border border-green-500'}`}>
                                            {row.highest_severity.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="p-4">
                                        <button className="text-blue-400 hover:text-blue-300 hover:underline text-sm font-semibold">
                                            View Details →
                                        </button>
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
