
import React, { useState, useEffect } from 'react';
import { Activity, Shield, Users, TrendingUp } from 'lucide-react';
import ModelStatusBadge from '../../components/stp/ModelStatusBadge';

const STPOverview = () => {
    // Mock Data (replace with API calls later)
    const stats = {
        activeAlerts: 3,
        psiScore: 0.045,
        modelMode: 'ACTIVE',
        lastInference: new Date().toISOString()
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800 dark:text-white">STP Surveillance Overview</h2>
                    <p className="text-sm text-slate-500">Streptococcus & Enterococcus Monitoring</p>
                </div>
                <ModelStatusBadge mode={stats.modelMode} />
            </div>

            {/* Disclaimer Banner */}
            <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-lg">
                <div className="flex gap-3">
                    <Shield className="w-5 h-5 text-amber-500" />
                    <p className="text-sm text-amber-800 font-medium">
                        ⚠ Surveillance System Only – Not for clinical decision-making. (M70 Policy Enforced)
                    </p>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">Active Alerts</p>
                            <h3 className="text-3xl font-bold text-slate-800 dark:text-gray-100 mt-2">{stats.activeAlerts}</h3>
                        </div>
                        <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg text-purple-600 dark:text-purple-400">
                            <Activity className="w-5 h-5" />
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">Drift (PSI)</p>
                            <h3 className="text-3xl font-bold text-slate-800 dark:text-gray-100 mt-2">{stats.psiScore}</h3>
                        </div>
                        <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg text-blue-600 dark:text-blue-400">
                            <TrendingUp className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-xs text-green-600 mt-2 font-medium">Stable (Below 0.1)</p>
                </div>

                <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">Monitored Wards</p>
                            <h3 className="text-3xl font-bold text-slate-800 dark:text-gray-100 mt-2">12</h3>
                        </div>
                        <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg text-green-600 dark:text-green-400">
                            <Users className="w-5 h-5" />
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 p-5 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">Last Update</p>
                            <h3 className="text-lg font-bold text-slate-800 dark:text-gray-100 mt-2">{new Date(stats.lastInference).toLocaleDateString()}</h3>
                        </div>
                        <div className="p-2 bg-gray-100 dark:bg-gray-700/50 rounded-lg text-gray-500">
                            <Activity className="w-5 h-5" />
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Placeholder for Quick Actions or recent activity */}
                <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm min-h-[300px] flex items-center justify-center text-slate-400 border-dashed border-2">
                    Map View or Quick Actions
                </div>
                <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm min-h-[300px] flex items-center justify-center text-slate-400 border-dashed border-2">
                    Recent System Logs
                </div>
            </div>
        </div>
    );
};

export default STPOverview;
