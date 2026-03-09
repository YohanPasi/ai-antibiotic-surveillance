import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Home, Activity, FileText, Database, Settings, LogOut, Brain, Beaker, Shield, ChevronDown, ChevronRight } from 'lucide-react';

const menuGroups = [
    {
        title: 'Non-Fermenters',
        subtitle: 'Pseudomonas & Acinetobacter',
        items: [
            { id: 'dashboard', label: 'Dashboard', icon: Home },
            // { id: 'audit_log', label: 'Audit Logs', icon: FileText },
        ],
    },
    {
        title: 'MRSA Prediction',
        subtitle: 'AI-Powered Detection',
        items: [
            { id: 'mrsa_prediction', label: 'MRSA AI', icon: Brain },
            //{ id: 'analytics', label: 'Governance', icon: Shield },
        ],
    },
    {
        title: 'ESBL Risk Engine',
        subtitle: 'Clinical Decision Support',
        items: [
            { id: 'esbl_cdss', label: 'Risk Assessment', icon: Shield },
            { id: 'esbl_audit', label: 'Stewardship Logs', icon: FileText },
            { id: 'esbl_lab_entry', label: 'Lab Results Entry', icon: Activity },
        ],
    },
    {
        title: 'STP Surveillance',
        subtitle: 'Streptococcus & Enterococcus',
        items: [
            //{ id: 'stp_dashboard', label: 'Overview', icon: Activity },
            { id: 'stp_ward_trends', label: 'Ward Trends', icon: Database },
            { id: 'stp_predictions', label: 'Early Warning', icon: Brain },
            { id: 'stp_alerts', label: 'Alerts & Review', icon: FileText },
            { id: 'stp_antibiogram_entry', label: 'Antibiogram Entry', icon: Beaker },
            // { id: 'stp_validation', label: 'Validation', icon: Shield },
            //{ id: 'stp_model_status', label: 'Model Status', icon: Activity },
        ],
    },
    {
        title: 'System',
        subtitle: 'Lab & Configuration',
        items: [
            { id: 'ast_entry', label: 'Lab Entry', icon: Beaker },
            { id: 'master_data', label: 'Master Data', icon: Database },
        ],
    },
];

const Sidebar = ({ activeView, setActiveView, logout }) => {
    const [expandedGroups, setExpandedGroups] = useState({
        'Non-Fermenters': false,
        'STP Surveillance': true,
        'MRSA Prediction': false,
        'ESBL Risk Engine': false,
        'System': false,
    });

    const toggle = title => setExpandedGroups(prev => ({ ...prev, [title]: !prev[title] }));

    return (
        <aside className="w-60 flex flex-col h-screen sticky top-0 flex-shrink-0 overflow-y-auto
                          bg-slate-50 dark:bg-gray-950 border-r border-slate-200 dark:border-white/5 text-slate-900 dark:text-white
                          scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-white/10 scrollbar-track-transparent">

            {/* Logo */}
            <div className="px-5 py-5 border-b border-slate-200 dark:border-white/5 flex items-center gap-3 flex-shrink-0">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600
                                flex items-center justify-center shadow-lg shadow-emerald-900/40 flex-shrink-0">
                    <span className="text-base font-extrabold text-slate-900 dark:text-white leading-none">S</span>
                </div>
                <div>
                    <h1 className="font-extrabold text-sm tracking-tight text-slate-900 dark:text-white leading-none">Sentinel</h1>
                    <p className="text-[10px] text-slate-500 dark:text-gray-500 uppercase tracking-[0.15em] mt-0.5">AMR Surveillance</p>
                </div>
            </div>

            {/* Nav groups */}
            <nav className="flex-1 py-3 px-3 space-y-0.5 overflow-y-auto">
                {menuGroups.map((group, gIdx) => {
                    const isExpanded = expandedGroups[group.title];
                    return (
                        <div key={gIdx} className="mb-1">
                            {/* Group header */}
                            <button
                                onClick={() => toggle(group.title)}
                                className="w-full flex items-center justify-between px-3 py-2 rounded-lg
                                           hover:bg-slate-200 dark:hover:bg-white/5 transition-all duration-150 group"
                            >
                                <div className="text-left">
                                    <p className="text-xs font-bold text-slate-700 dark:text-gray-300 group-hover:text-slate-900 dark:text-white transition-colors">
                                        {group.title}
                                    </p>
                                    {group.subtitle && (
                                        <p className="text-[10px] text-slate-400 dark:text-gray-600 mt-0.5">{group.subtitle}</p>
                                    )}
                                </div>
                                {isExpanded
                                    ? <ChevronDown className="w-3.5 h-3.5 text-slate-400 dark:text-gray-600 flex-shrink-0" />
                                    : <ChevronRight className="w-3.5 h-3.5 text-slate-400 dark:text-gray-600 flex-shrink-0" />}
                            </button>

                            {/* Items */}
                            <AnimatePresence initial={false}>
                                {isExpanded && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                        className="overflow-hidden"
                                    >
                                        <div className="mt-0.5 space-y-0.5 pl-2 border-l border-slate-200 dark:border-white/5 ml-3">
                                            {group.items.map(item => {
                                                const Icon = item.icon;
                                                const isActive = activeView === item.id;
                                                return (
                                                    <button
                                                        key={item.id}
                                                        onClick={() => setActiveView(item.id)}
                                                        className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium
                                                                    transition-all duration-150
                                                                    ${isActive
                                                                ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/20'
                                                                : 'text-slate-500 dark:text-gray-500 hover:bg-slate-200 dark:hover:bg-white/5 hover:text-slate-900 dark:text-gray-200'}`}
                                                    >
                                                        <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-emerald-400' : 'text-slate-400 dark:text-gray-600'}`} />
                                                        {item.label}
                                                        {isActive && (
                                                            <span className="ml-auto w-1 h-1 rounded-full bg-emerald-400" />
                                                        )}
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    );
                })}

                {/* Settings */}
                <div className="pt-2 border-t border-slate-200 dark:border-white/5">
                    <button
                        onClick={() => setActiveView('settings')}
                        className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-150
                            ${activeView === 'settings'
                                ? 'bg-slate-200 dark:bg-white/10 text-slate-900 dark:text-white'
                                : 'text-slate-500 dark:text-gray-500 hover:bg-slate-200 dark:hover:bg-white/5 hover:text-slate-900 dark:text-gray-200'}`}
                    >
                        <Settings className="w-3.5 h-3.5 text-slate-400 dark:text-gray-600" />
                        Settings
                    </button>
                </div>
            </nav>

            {/* Footer / Logout */}
            <div className="px-3 py-3 border-t border-slate-200 dark:border-white/5 flex-shrink-0">
                <button
                    onClick={logout}
                    className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-xs font-semibold
                               text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-500/10 hover:text-red-700 dark:hover:text-red-300
                               border border-transparent hover:border-red-200 dark:hover:border-red-500/20
                               transition-all duration-150"
                >
                    <LogOut className="w-3.5 h-3.5" />
                    Sign Out
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
