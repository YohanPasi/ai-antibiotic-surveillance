import React from 'react';
import { Shield, Clock, Activity, RefreshCw } from 'lucide-react';

const STATUS_MAP = {
    'ACTIVE': { icon: <Shield className="w-3.5 h-3.5" />, label: 'Surveillance Active', className: 'bg-emerald-100 border-emerald-300 text-emerald-700' },
    'SHADOW': { icon: <Clock className="w-3.5 h-3.5" />, label: 'In Testing', className: 'bg-blue-100 border-blue-300 text-blue-700' },
    'CALIBRATING': { icon: <Activity className="w-3.5 h-3.5" />, label: 'Calibrating', className: 'bg-amber-100 border-amber-300 text-amber-700' },
    'RETRAINING': { icon: <RefreshCw className="w-3.5 h-3.5 animate-spin" />, label: 'Updating', className: 'bg-purple-100 border-purple-300 text-purple-700' },
};

/**
 * ModelStatusBadge — shows surveillance system status in plain English.
 * mode: 'ACTIVE' | 'SHADOW' | 'CALIBRATING' | 'RETRAINING'
 */
const ModelStatusBadge = ({ mode = 'ACTIVE' }) => {
    const cfg = STATUS_MAP[mode?.toUpperCase()] || STATUS_MAP['ACTIVE'];
    return (
        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-semibold ${cfg.className}`}>
            {cfg.icon}
            {cfg.label}
        </div>
    );
};

export default ModelStatusBadge;
