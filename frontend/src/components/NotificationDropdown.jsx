import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, X, AlertTriangle, CheckCircle, Info } from 'lucide-react';

const typeConfig = {
    alert: { icon: AlertTriangle, ring: 'ring-red-500/20', dot: 'bg-red-400', text: 'text-red-400' },
    success: { icon: CheckCircle, ring: 'ring-emerald-500/20', dot: 'bg-emerald-400', text: 'text-emerald-400' },
    info: { icon: Info, ring: 'ring-blue-500/20', dot: 'bg-blue-400', text: 'text-blue-400' },
};

const NotificationDropdown = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [notifications, setNotifications] = useState([
        { id: 1, type: 'alert', title: 'MRSA Alert', message: 'High risk prediction in ICU Ward 3', time: '5 min ago', read: false },
        { id: 2, type: 'success', title: 'Report Generated', message: 'Weekly surveillance report is ready', time: '1 hour ago', read: false },
        { id: 3, type: 'info', title: 'System Update', message: 'New ESBL model deployed successfully', time: '3 hours ago', read: true },
        { id: 4, type: 'alert', title: 'Outbreak Warning', message: 'Unusual spike in Non-Fermenters detected', time: '1 day ago', read: true },
    ]);

    const unreadCount = notifications.filter(n => !n.read).length;
    const markAsRead = id => setNotifications(ns => ns.map(n => n.id === id ? { ...n, read: true } : n));
    const markAll = () => setNotifications(ns => ns.map(n => ({ ...n, read: true })));
    const clear = id => setNotifications(ns => ns.filter(n => n.id !== id));

    return (
        <div className="relative">
            {/* Bell button */}
            <button
                onClick={() => setIsOpen(o => !o)}
                className="relative w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5
                           flex items-center justify-center text-gray-400 hover:text-white
                           transition-all duration-200"
            >
                <Bell className="w-4 h-4" />
                {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[10px]
                                     font-bold rounded-full flex items-center justify-center border border-gray-950">
                        {unreadCount}
                    </span>
                )}
            </button>

            {/* Backdrop */}
            {isOpen && (
                <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
            )}

            {/* Panel */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.97, y: -8 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.97, y: -8 }}
                        transition={{ duration: 0.15, ease: 'easeOut' }}
                        className="absolute right-0 mt-2 w-96 rounded-2xl border border-white/10
                                   bg-gray-950 shadow-2xl shadow-black/60 z-50 overflow-hidden"
                        style={{ backdropFilter: 'blur(12px)' }}
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
                            <div>
                                <h3 className="text-sm font-bold text-white">Notifications</h3>
                                {unreadCount > 0 && (
                                    <p className="text-xs text-gray-500 mt-0.5">{unreadCount} unread</p>
                                )}
                            </div>
                            {unreadCount > 0 && (
                                <button onClick={markAll}
                                    className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition-colors">
                                    Mark all read
                                </button>
                            )}
                        </div>

                        {/* List */}
                        <div className="max-h-80 overflow-y-auto divide-y divide-white/[0.04]">
                            {notifications.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-12 gap-3 text-gray-600">
                                    <Bell className="w-8 h-8 opacity-30" />
                                    <p className="text-sm">No notifications</p>
                                </div>
                            ) : notifications.map(n => {
                                const cfg = typeConfig[n.type] ?? typeConfig.info;
                                const Icon = cfg.icon;
                                return (
                                    <div
                                        key={n.id}
                                        onClick={() => markAsRead(n.id)}
                                        className={`flex items-start gap-3 px-5 py-3.5 cursor-pointer transition-colors duration-150
                                                    hover:bg-white/[0.03] ${!n.read ? 'bg-white/[0.02]' : ''}`}
                                    >
                                        <div className={`mt-0.5 w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0
                                                         ring-1 ${cfg.ring} bg-white/5`}>
                                            <Icon className={`w-3.5 h-3.5 ${cfg.text}`} strokeWidth={2} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-1.5 mb-0.5">
                                                <p className="text-sm font-semibold text-white truncate">{n.title}</p>
                                                {!n.read && (
                                                    <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
                                                )}
                                            </div>
                                            <p className="text-xs text-gray-400 leading-snug">{n.message}</p>
                                            <p className="text-[10px] text-gray-600 mt-1">{n.time}</p>
                                        </div>
                                        <button
                                            onClick={e => { e.stopPropagation(); clear(n.id); }}
                                            className="text-gray-700 hover:text-gray-300 transition-colors mt-0.5 flex-shrink-0"
                                        >
                                            <X className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Footer */}
                        <div className="px-5 py-3 border-t border-white/5 bg-white/[0.02]">
                            <button className="w-full text-center text-xs font-semibold text-gray-500 hover:text-gray-300 transition-colors">
                                View all notifications
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default NotificationDropdown;
