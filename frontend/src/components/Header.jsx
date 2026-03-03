import { User, Sun, Moon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import NotificationDropdown from './NotificationDropdown';

const Header = () => {
    const { user } = useAuth();
    const { darkMode, toggleTheme } = useTheme();

    return (
        <header className="h-14 flex items-center justify-between px-6 sticky top-0 z-40
                           bg-gray-950/80 backdrop-blur-md border-b border-white/5
                           transition-all duration-300 flex-shrink-0">

            {/* Left: breadcrumb / title */}
            <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-gray-300">AMR Surveillance Platform</span>
                <span className="hidden sm:block w-px h-4 bg-white/10" />
                <span className="hidden sm:flex items-center gap-1.5 text-xs text-gray-600">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Live
                </span>
            </div>

            {/* Right controls */}
            <div className="flex items-center gap-2">

                {/* Theme toggle */}
                <button
                    onClick={toggleTheme}
                    className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5
                               flex items-center justify-center text-gray-400 hover:text-white
                               transition-all duration-200"
                    title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                >
                    {darkMode
                        ? <Sun className="w-4 h-4" />
                        : <Moon className="w-4 h-4" />}
                </button>

                {/* Notifications */}
                <NotificationDropdown />

                {/* Divider */}
                <span className="w-px h-5 bg-white/10 mx-1" />

                {/* User chip */}
                <div className="flex items-center gap-2.5 pl-1">
                    <div className="text-right hidden sm:block">
                        <p className="text-xs font-bold text-gray-200 leading-none">{user?.username || 'Guest'}</p>
                        <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mt-0.5">
                            {user?.role || 'Viewer'}
                        </p>
                    </div>
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700
                                    border border-white/10 flex items-center justify-center shadow-md">
                        <User className="w-4 h-4 text-white" strokeWidth={2} />
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
