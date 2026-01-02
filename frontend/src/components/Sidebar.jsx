import { Home, Activity, FileText, Database, Settings, LogOut, Brain } from 'lucide-react';

const Sidebar = ({ activeView, setActiveView, logout }) => {

    const menuItems = [
        { id: 'dashboard', label: 'Dashboard', icon: Home },
        { id: 'mrsa_prediction', label: 'MRSA AI (Stage F)', icon: Brain },
        { id: 'ward_detail', label: 'Ward Detail', icon: Activity }, // Note: Often better to navigate via context, but providing direct link
        { id: 'audit_log', label: 'Audit Logs', icon: FileText },
        // { id: 'manual_entry', label: 'Data Entry', icon: Database }, // This is usually a modal, but could be a page. Button is in dashboard. 
    ];

    return (
        <aside className="w-64 bg-gray-900 border-r border-gray-800 text-white flex flex-col h-screen sticky top-0">
            <div className="p-6 border-b border-gray-800 flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-purple-900/50">
                    <span className="text-lg font-bold">A</span>
                </div>
                <div>
                    <h1 className="font-bold text-lg tracking-tight">Antigravity</h1>
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider">Surveillance</p>
                </div>
            </div>

            <nav className="flex-1 p-4 space-y-2">
                <p className="text-xs font-semibold text-gray-500 uppercase px-4 mb-2 mt-4">Main Menu</p>
                {menuItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeView === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => setActiveView(item.id)}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${isActive
                                ? 'bg-purple-600/20 text-purple-300 border border-purple-500/30'
                                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                                }`}
                        >
                            <Icon className={`w-5 h-5 ${isActive ? 'text-purple-400' : 'text-gray-500'}`} />
                            {item.label}
                        </button>
                    );
                })}

                <p className="text-xs font-semibold text-gray-500 uppercase px-4 mb-2 mt-8">System</p>
                <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-400 hover:bg-gray-800 hover:text-white transition-colors">
                    <Settings className="w-5 h-5 text-gray-500" />
                    Settings
                </button>
            </nav>

            <div className="p-4 border-t border-gray-800">
                <button
                    onClick={logout}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-red-400 hover:bg-red-900/20 transition-colors"
                >
                    <LogOut className="w-5 h-5" />
                    Sign Out
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
