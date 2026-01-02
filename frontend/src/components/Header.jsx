import React from 'react';
import { User, Bell, Search } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Header = () => {
    const { user } = useAuth();

    return (
        <header className="h-16 bg-gray-900/50 backdrop-blur-md border-b border-gray-800 flex items-center justify-between px-6 sticky top-0 z-40">
            {/* Left: Operations/Breadcrumb (Placeholder) */}
            <div className="flex items-center gap-4">
                <div className="relative group">
                    <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-500 group-focus-within:text-purple-400 transition-colors" />
                    <input
                        type="text"
                        placeholder="Search isolate, ward..."
                        className="bg-gray-800/50 text-sm text-gray-300 rounded-full pl-10 pr-4 py-2 border border-transparent focus:border-purple-500/50 focus:bg-gray-800 focus:outline-none w-64 transition-all"
                    />
                </div>
            </div>

            {/* Right: User Profile & Status */}
            <div className="flex items-center gap-6">
                {/* Status Indicator */}
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-900/10 border border-green-900/30">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    <span className="text-xs font-medium text-green-400">System Online</span>
                </div>

                {/* Notifications */}
                <button className="relative text-gray-400 hover:text-white transition-colors">
                    <Bell className="w-5 h-5" />
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full border border-gray-900"></span>
                </button>

                <div className="h-6 w-px bg-gray-800"></div>

                {/* User Profile */}
                <div className="flex items-center gap-3">
                    <div className="text-right hidden md:block">
                        <p className="text-sm font-bold text-gray-200 leading-none">{user?.username || 'Guest'}</p>
                        <p className="text-[10px] font-medium text-gray-500 uppercase mt-1">{user?.role || 'Viewer'}</p>
                    </div>
                    <div className="w-9 h-9 bg-gray-800 rounded-full flex items-center justify-center border border-gray-700 shadow-sm overflow-hidden">
                        <User className="w-5 h-5 text-gray-400" />
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
