import React, { useState } from 'react';
import { Home, Activity, FileText, Database, Settings, LogOut, Brain, Beaker, Shield, ChevronDown, ChevronRight } from 'lucide-react';

const Sidebar = ({ activeView, setActiveView, logout }) => {

    const menuGroups = [
        {
            title: "Non-Fermenters",
            subtitle: "Pseudomonas & Acinetobacter",
            items: [
                { id: 'dashboard', label: 'Dashboard', icon: Home },
                { id: 'ward_detail', label: 'Ward Detail', icon: Activity },
                { id: 'audit_log', label: 'Audit Logs', icon: FileText },
            ]
        },
        {
            title: "MRSA Prediction",
            subtitle: "AI-Powered Detection",
            items: [
                { id: 'mrsa_prediction', label: 'MRSA AI', icon: Brain },
                { id: 'analytics', label: 'Governance', icon: Shield },
            ]
        },
        {
            title: "ESBL Risk Engine",
            subtitle: "Clinical Decision Support",
            items: [
                { id: 'esbl_cdss', label: 'Risk Assessment', icon: Shield },
                { id: 'esbl_audit', label: 'Stewardship Logs', icon: FileText },
                { id: 'esbl_lab_entry', label: 'Lab Results Entry', icon: Activity },
            ]
        },
        {
            title: "STP Surveillance",
            subtitle: "Streptococcus & Enterococcus",
            items: [
                { id: 'stp_dashboard', label: 'Overview', icon: Activity },
                { id: 'stp_ward_trends', label: 'Ward Trends', icon: Database },
                { id: 'stp_predictions', label: 'Early Warning', icon: Brain },
                { id: 'stp_alerts', label: 'Alerts & Review', icon: FileText },
                { id: 'stp_antibiogram_entry', label: 'Antibiogram Entry', icon: Beaker },
                { id: 'stp_validation', label: 'Validation', icon: Shield },
                { id: 'stp_model_status', label: 'Model Status', icon: Activity }
            ]
        },
        {
            title: "System",
            subtitle: "Lab & Configuration",
            items: [
                { id: 'ast_entry', label: 'Lab Entry', icon: Beaker },
                { id: 'master_data', label: 'Master Data', icon: Database },
            ]
        }
    ];

    const [expandedGroups, setExpandedGroups] = useState({
        "Non-Fermenters": false,
        "STP Surveillance": true,
        "MRSA Prediction": false,
        "ESBL Risk Engine": false,
        "System": false
    });

    const toggleGroup = (title) => {
        setExpandedGroups(prev => ({ ...prev, [title]: !prev[title] }));
    };

    return (
        <aside className="w-64 flex flex-col h-screen sticky top-0 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-800 border-r transition-colors duration-300
            bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 text-slate-800 dark:text-white">
            <div className="p-6 border-b border-gray-200 dark:border-gray-800 flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-emerald-600 to-teal-600 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-900/20">
                    <span className="text-lg font-bold text-white">S</span>
                </div>
                <div>
                    <h1 className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">Sentinel</h1>
                    <p className="text-[10px] text-slate-500 dark:text-gray-500 uppercase tracking-wider">AMR Surveillance</p>
                </div>
            </div>

            <nav className="flex-1 p-4 space-y-4">
                {menuGroups.map((group, groupIdx) => {
                    const isExpanded = expandedGroups[group.title];
                    return (
                        <div key={groupIdx}>
                            <button
                                onClick={() => toggleGroup(group.title)}
                                className="w-full flex items-center justify-between px-4 mb-2 py-1.5 rounded-md transition-all duration-200
                                    hover:bg-gray-100 dark:hover:bg-gray-800/50"
                            >
                                <div className="flex flex-col items-start">
                                    <span className="text-sm font-semibold text-slate-800 dark:text-gray-200">
                                        {group.title}
                                    </span>
                                    {group.subtitle && (
                                        <span className="text-[10px] text-slate-500 dark:text-gray-500 font-medium">
                                            {group.subtitle}
                                        </span>
                                    )}
                                </div>
                                {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                            </button>

                            {isExpanded && (
                                <div className="space-y-1 animate-fadeIn">
                                    {group.items.map((item) => {
                                        const Icon = item.icon;
                                        const isActive = activeView === item.id;
                                        return (
                                            <button
                                                key={item.id}
                                                onClick={() => setActiveView(item.id)}
                                                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${isActive
                                                    ? 'bg-emerald-100 dark:bg-emerald-600/20 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/30'
                                                    : 'text-slate-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-slate-900 dark:hover:text-white'
                                                    }`}
                                            >
                                                <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400 dark:text-gray-500'}`} />
                                                {item.label}
                                            </button>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    );
                })}

                <div>
                    <p className="text-xs font-bold text-slate-500 dark:text-gray-500 uppercase px-4 mb-3 tracking-wider">System</p>
                    <button className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors
                        text-slate-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-slate-900 dark:hover:text-white">
                        <Settings className="w-4 h-4 text-slate-400 dark:text-gray-500" />
                        Settings
                    </button>
                </div>
            </nav>

            <div className="p-4 border-t border-gray-200 dark:border-gray-800">
                <button
                    onClick={logout}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                >
                    <LogOut className="w-5 h-5" />
                    Sign Out
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
