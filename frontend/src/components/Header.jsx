import { User, Bell, Search, Sun, Moon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const Header = () => {
    const { user } = useAuth();
    const { darkMode, toggleTheme } = useTheme();

    return (
        <header className="h-16 flex items-center justify-between px-6 sticky top-0 z-40 transition-colors duration-300
            bg-white/80 dark:bg-gray-900/50 backdrop-blur-md border-b border-gray-200 dark:border-gray-800 text-gray-800 dark:text-gray-100">
            {/* Left: Operations/Breadcrumb (Placeholder) */}
            <div className="flex items-center gap-4">
                <div className="relative group">
                    <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400 dark:text-gray-500 group-focus-within:text-purple-500 dark:group-focus-within:text-purple-400 transition-colors" />
                    <input
                        type="text"
                        placeholder="Search isolate, ward..."
                        className="text-sm rounded-full pl-10 pr-4 py-2 border border-transparent focus:outline-none w-64 transition-all
                        bg-gray-100 dark:bg-gray-800/50 text-gray-800 dark:text-gray-300
                        focus:border-purple-500 focus:bg-white dark:focus:bg-gray-800"
                    />
                </div>
            </div>

            {/* Right: User Profile & Status */}
            <div className="flex items-center gap-6">
                {/* Theme Toggle */}
                <button
                    onClick={toggleTheme}
                    className="p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
                >
                    {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>

                {/* Status Indicator */}
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-100 dark:bg-green-900/10 border border-green-200 dark:border-green-900/30">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    <span className="text-xs font-medium text-green-700 dark:text-green-400">System Online</span>
                </div>

                {/* Notifications */}
                <button className="relative text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                    <Bell className="w-5 h-5" />
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full border border-white dark:border-gray-900"></span>
                </button>

                <div className="h-6 w-px bg-gray-200 dark:bg-gray-800"></div>

                {/* User Profile */}
                <div className="flex items-center gap-3">
                    <div className="text-right hidden md:block">
                        <p className="text-sm font-bold text-gray-800 dark:text-gray-200 leading-none">{user?.username || 'Guest'}</p>
                        <p className="text-[10px] font-medium text-gray-500 uppercase mt-1">{user?.role || 'Viewer'}</p>
                    </div>
                    <div className="w-9 h-9 rounded-full flex items-center justify-center border shadow-sm overflow-hidden
                        bg-gray-100 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                        <User className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                    </div>
                </div>
            </div>
        </header>
    ); // Removed original 'export default Header;' since I replaced the whole body essentially. Wait no, replace tool replaces range.
};

export default Header;
