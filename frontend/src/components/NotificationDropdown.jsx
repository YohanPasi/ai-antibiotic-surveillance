import React, { useState } from 'react';
import { Bell, X } from 'lucide-react';

const NotificationDropdown = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [notifications, setNotifications] = useState([
        { id: 1, type: 'alert', title: 'MRSA Alert', message: 'High risk prediction in ICU Ward 3', time: '5 min ago', read: false },
        { id: 2, type: 'success', title: 'Report Generated', message: 'Weekly surveillance report is ready', time: '1 hour ago', read: false },
        { id: 3, type: 'info', title: 'System Update', message: 'New ESBL model deployed successfully', time: '3 hours ago', read: true },
        { id: 4, type: 'alert', title: 'Outbreak Warning', message: 'Unusual spike in Non-Fermenters detected', time: '1 day ago', read: true }
    ]);

    const unreadCount = notifications.filter(n => !n.read).length;

    const markAsRead = (id) => {
        setNotifications(notifications.map(n => n.id === id ? { ...n, read: true } : n));
    };

    const markAllAsRead = () => {
        setNotifications(notifications.map(n => ({ ...n, read: true })));
    };

    const clearNotification = (id) => {
        setNotifications(notifications.filter(n => n.id !== id));
    };

    const getTypeStyles = (type) => {
        switch (type) {
            case 'alert':
                return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
            case 'success':
                return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
            case 'info':
                return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
            default:
                return 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700';
        }
    };

    return (
        <div className="relative">
            {/* Bell Icon */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="relative text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
            >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center border-2 border-white dark:border-gray-900">
                        {unreadCount}
                    </span>
                )}
            </button>

            {/* Dropdown */}
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)}></div>

                    {/* Notification Panel */}
                    <div className="absolute right-0 mt-2 w-96 bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-800 z-50 overflow-hidden">
                        {/* Header */}
                        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
                            <div>
                                <h3 className="font-bold text-gray-900 dark:text-white">Notifications</h3>
                                {unreadCount > 0 && (
                                    <p className="text-xs text-gray-600 dark:text-gray-400">{unreadCount} unread</p>
                                )}
                            </div>
                            {unreadCount > 0 && (
                                <button
                                    onClick={markAllAsRead}
                                    className="text-xs text-emerald-600 dark:text-emerald-400 hover:underline font-medium"
                                >
                                    Mark all as read
                                </button>
                            )}
                        </div>

                        {/* Notifications List */}
                        <div className="max-h-96 overflow-y-auto">
                            {notifications.length === 0 ? (
                                <div className="p-8 text-center">
                                    <Bell className="w-12 h-12 text-gray-300 dark:text-gray-700 mx-auto mb-3" />
                                    <p className="text-gray-500 dark:text-gray-400 text-sm">No notifications</p>
                                </div>
                            ) : (
                                notifications.map((notification) => (
                                    <div
                                        key={notification.id}
                                        className={`p-4 border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors ${!notification.read ? 'bg-emerald-50/50 dark:bg-emerald-900/10' : ''
                                            }`}
                                        onClick={() => markAsRead(notification.id)}
                                    >
                                        <div className="flex items-start justify-between gap-3">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <h4 className="font-semibold text-sm text-gray-900 dark:text-white truncate">
                                                        {notification.title}
                                                    </h4>
                                                    {!notification.read && (
                                                        <span className="w-2 h-2 bg-emerald-500 rounded-full flex-shrink-0"></span>
                                                    )}
                                                </div>
                                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                                                    {notification.message}
                                                </p>
                                                <p className="text-xs text-gray-500 dark:text-gray-500">
                                                    {notification.time}
                                                </p>
                                            </div>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    clearNotification(notification.id);
                                                }}
                                                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 flex-shrink-0"
                                            >
                                                <X className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        {/* Footer */}
                        <div className="p-3 bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-800 text-center">
                            <button className="text-sm text-emerald-600 dark:text-emerald-400 hover:underline font-medium">
                                View all notifications
                            </button>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default NotificationDropdown;
