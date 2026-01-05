import React, { useState } from 'react';
import { Home, Activity, FileText, Database, Settings, LogOut, Brain, Beaker, Shield, ChevronDown, ChevronRight } from 'lucide-react';

const Sidebar = ({ activeView, setActiveView, logout }) => {

    const menuGroups = [
        {
            title: "Non-Fermenter Surveillance",
            items: [
                { id: 'dashboard', label: 'Dashboard', icon: Home },
                { id: 'ward_detail', label: 'Ward Detail', icon: Activity },
                { id: 'audit_log', label: 'Audit Logs', icon: FileText },
            ]
        },
        {
            title: "MRSA Control (AI)",
            items: [
                { id: 'mrsa_prediction', label: 'MRSA AI', icon: Brain },
                { id: 'analytics', label: 'Governance', icon: Shield },
            ]
        },
        {
            title: "Clinical Decision Support",
            items: [
                { id: 'esbl_cdss', label: 'ESBL Risk Engine', icon: Shield },
                { id: 'esbl_audit', label: 'Stewardship Logs', icon: FileText },
            ]
        },
        {
            title: "Lab & Configuration",
            items: [
                { id: 'ast_entry', label: 'Lab Entry', icon: Beaker },
                { id: 'master_data', label: 'Master Data', icon: Database },
            ]
        }
    ];

    const [expandedGroups, setExpandedGroups] = useState({
        "Non-Fermenter Surveillance": false,
        "MRSA Control (AI)": false,
        "Clinical Decision Support": true, // Auto-expand for visibility
        "Lab & Configuration": false
    });

    const toggleGroup = (title) => {
        setExpandedGroups(prev => ({ ...prev, [title]: !prev[title] }));
    };

    return (
        <aside className="w-64 flex flex-col h-screen sticky top-0 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-800 border-r transition-colors duration-300
            bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-800 text-slate-800 dark:text-white">
            <div className="p-6 border-b border-gray-200 dark:border-gray-800 flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-purple-900/20">
                    <span className="text-lg font-bold text-white">A</span>
                </div>
                <div>
                    <h1 className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">Antigravity</h1>
                    <p className="text-[10px] text-slate-500 dark:text-gray-500 uppercase tracking-wider">Surveillance</p>
                </div>
            </div>

            <nav className="flex-1 p-4 space-y-4">
                {menuGroups.map((group, groupIdx) => {
                    const isExpanded = expandedGroups[group.title];
                    return (
                        <div key={groupIdx}>
                            <button
                                onClick={() => toggleGroup(group.title)}
                                className="w-full flex items-center justify-between text-xs font-bold px-4 mb-2 tracking-wider transition-colors uppercase
                                    text-slate-500 hover:text-slate-800 
                                    dark:text-gray-500 dark:hover:text-gray-300"
                            >
                                {group.title}
                                {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
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
                                                    ? 'bg-purple-100 dark:bg-purple-600/20 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-500/30'
                                                    : 'text-slate-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-slate-900 dark:hover:text-white'
                                                    }`}
                                            >
                                                <Icon className={`w-4 h-4 ${isActive ? 'text-purple-600 dark:text-purple-400' : 'text-slate-400 dark:text-gray-500'}`} />
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
