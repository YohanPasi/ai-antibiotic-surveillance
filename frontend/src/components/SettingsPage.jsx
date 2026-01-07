import React, { useState } from 'react';
import { X, User, Bell, Shield, Palette, Globe, Save, CheckCircle2 } from 'lucide-react';

const SettingsPage = ({ onClose }) => {
    const [activeTab, setActiveTab] = useState('profile');
    const [saved, setSaved] = useState(false);
    const [settings, setSettings] = useState({
        // Profile
        displayName: 'Dr. Admin User',
        email: 'admin@sentinel.health',
        role: 'Senior Clinician',
        department: 'Infection Control',

        // Notifications
        emailNotifications: true,
        pushNotifications: true,
        alertThreshold: 'medium',
        dailyDigest: true,

        // Appearance
        theme: 'system',
        compactMode: false,
        animationsEnabled: true,

        // Privacy
        shareAnonymousData: false,
        auditLogging: true,
        sessionTimeout: 30
    });

    const handleSave = () => {
        // Save settings logic here
        localStorage.setItem('sentinelSettings', JSON.stringify(settings));
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
    };

    const tabs = [
        { id: 'profile', label: 'Profile', icon: User },
        { id: 'notifications', label: 'Notifications', icon: Bell },
        { id: 'appearance', label: 'Appearance', icon: Palette },
        { id: 'privacy', label: 'Privacy & Security', icon: Shield }
    ];

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-800">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h2>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Manage your account and preferences</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                <div className="flex flex-1 overflow-hidden">
                    {/* Sidebar */}
                    <div className="w-64 border-r border-gray-200 dark:border-gray-800 p-4 overflow-y-auto">
                        <nav className="space-y-1">
                            {tabs.map((tab) => {
                                const Icon = tab.icon;
                                const isActive = activeTab === tab.id;
                                return (
                                    <button
                                        key={tab.id}
                                        onClick={() => setActiveTab(tab.id)}
                                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${isActive
                                                ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-700'
                                                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                                            }`}
                                    >
                                        <Icon className="w-5 h-5" />
                                        {tab.label}
                                    </button>
                                );
                            })}
                        </nav>
                    </div>

                    {/* Content */}
                    <div className="flex-1 p-6 overflow-y-auto">
                        {activeTab === 'profile' && (
                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                        Display Name
                                    </label>
                                    <input
                                        type="text"
                                        value={settings.displayName}
                                        onChange={(e) => setSettings({ ...settings, displayName: e.target.value })}
                                        className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                        Email
                                    </label>
                                    <input
                                        type="email"
                                        value={settings.email}
                                        onChange={(e) => setSettings({ ...settings, email: e.target.value })}
                                        className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                        Role
                                    </label>
                                    <input
                                        type="text"
                                        value={settings.role}
                                        onChange={(e) => setSettings({ ...settings, role: e.target.value })}
                                        className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                        Department
                                    </label>
                                    <select
                                        value={settings.department}
                                        onChange={(e) => setSettings({ ...settings, department: e.target.value })}
                                        className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                                    >
                                        <option>Infection Control</option>
                                        <option>Microbiology</option>
                                        <option>ICU</option>
                                        <option>General Ward</option>
                                        <option>Administration</option>
                                    </select>
                                </div>
                            </div>
                        )}

                        {activeTab === 'notifications' && (
                            <div className="space-y-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="font-semibold text-gray-900 dark:text-white">Email Notifications</p>
                                        <p className="text-sm text-gray-600 dark:text-gray-400">Receive alerts via email</p>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={settings.emailNotifications}
                                            onChange={(e) => setSettings({ ...settings, emailNotifications: e.target.checked })}
                                            className="sr-only peer"
                                        />
                                        <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-emerald-300 dark:peer-focus:ring-emerald-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-emerald-600"></div>
                                    </label>
                                </div>

                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="font-semibold text-gray-900 dark:text-white">Push Notifications</p>
                                        <p className="text-sm text-gray-600 dark:text-gray-400">Browser notifications for critical alerts</p>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={settings.pushNotifications}
                                            onChange={(e) => setSettings({ ...settings, pushNotifications: e.target.checked })}
                                            className="sr-only peer"
                                        />
                                        <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-emerald-300 dark:peer-focus:ring-emerald-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-emerald-600"></div>
                                    </label>
                                </div>

                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                        Alert Threshold
                                    </label>
                                    <select
                                        value={settings.alertThreshold}
                                        onChange={(e) => setSettings({ ...settings, alertThreshold: e.target.value })}
                                        className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                                    >
                                        <option value="low">Low - All alerts</option>
                                        <option value="medium">Medium - Important only</option>
                                        <option value="high">High - Critical only</option>
                                    </select>
                                </div>
                            </div>
                        )}

                        {activeTab === 'appearance' && (
                            <div className="space-y-6">
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                        Theme
                                    </label>
                                    <div className="grid grid-cols-3 gap-3">
                                        {['light', 'dark', 'system'].map((theme) => (
                                            <button
                                                key={theme}
                                                onClick={() => setSettings({ ...settings, theme })}
                                                className={`px-4 py-3 rounded-lg border-2 transition-all capitalize ${settings.theme === theme
                                                        ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                                                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                                                    }`}
                                            >
                                                {theme}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="font-semibold text-gray-900 dark:text-white">Compact Mode</p>
                                        <p className="text-sm text-gray-600 dark:text-gray-400">Reduce spacing and padding</p>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={settings.compactMode}
                                            onChange={(e) => setSettings({ ...settings, compactMode: e.target.checked })}
                                            className="sr-only peer"
                                        />
                                        <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-emerald-300 dark:peer-focus:ring-emerald-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-emerald-600"></div>
                                    </label>
                                </div>
                            </div>
                        )}

                        {activeTab === 'privacy' && (
                            <div className="space-y-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="font-semibold text-gray-900 dark:text-white">Audit Logging</p>
                                        <p className="text-sm text-gray-600 dark:text-gray-400">Track all system activities</p>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={settings.auditLogging}
                                            onChange={(e) => setSettings({ ...settings, auditLogging: e.target.checked })}
                                            className="sr-only peer"
                                        />
                                        <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-emerald-300 dark:peer-focus:ring-emerald-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-emerald-600"></div>
                                    </label>
                                </div>

                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                        Session Timeout (minutes)
                                    </label>
                                    <input
                                        type="number"
                                        value={settings.sessionTimeout}
                                        onChange={(e) => setSettings({ ...settings, sessionTimeout: parseInt(e.target.value) })}
                                        className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                                        min="5"
                                        max="120"
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50">
                    {saved && (
                        <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
                            <CheckCircle2 className="w-5 h-5" />
                            <span className="text-sm font-medium">Settings saved successfully!</span>
                        </div>
                    )}
                    {!saved && <div></div>}
                    <div className="flex items-center gap-3">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSave}
                            className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg hover:from-emerald-700 hover:to-teal-700 transition-all shadow-lg"
                        >
                            <Save className="w-4 h-4" />
                            Save Changes
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SettingsPage;
