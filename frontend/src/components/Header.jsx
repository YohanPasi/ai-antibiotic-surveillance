import { User, Sun, Moon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import NotificationDropdown from './NotificationDropdown';

const Header = () => {
    const { user } = useAuth();
    const { darkMode, toggleTheme } = useTheme();

    return (
        <header className="h-16 flex items-center justify-between px-6 sticky top-0 z-40 transition-colors duration-300
            bg-white/80 dark:bg-gray-900/50 backdrop-blur-md border-b border-gray-200 dark:border-gray-800 text-gray-800 dark:text-gray-100">
            {/* Left: Empty for now */}
            <div className="flex items-center gap-4">
                <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300">AMR Surveillance Platform</h2>
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

                {/* Notifications */}
                <NotificationDropdown />

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
