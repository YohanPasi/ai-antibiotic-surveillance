
import React from 'react';
import { Shield, Eye } from 'lucide-react';

const ModelStatusBadge = ({ mode }) => {
    // mode: ACTIVE, SHADOW, RETIRED

    if (mode === 'SHADOW') {
        return (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-gray-100 border border-gray-200 text-gray-600 rounded-full text-xs font-bold uppercase tracking-wider">
                <Eye className="w-3 h-3" />
                Shadow Mode
            </div>
        );
    }

    if (mode === 'ACTIVE') {
        return (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-green-100 border border-green-200 text-green-700 rounded-full text-xs font-bold uppercase tracking-wider">
                <Shield className="w-3 h-3" />
                Active Surveillance
            </div>
        );
    }

    return null;
};

export default ModelStatusBadge;
