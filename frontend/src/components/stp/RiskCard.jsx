
import React from 'react';
import { AlertTriangle, TrendingUp, HelpCircle } from 'lucide-react';

const RiskCard = ({ ward, organism, antibiotic, probability, riskLevel, uncertainty, horizon }) => {
    // Risk color logic
    const getColor = (level) => {
        switch (level?.toLowerCase()) {
            case 'high': return 'bg-red-50 text-red-700 border-red-200';
            case 'medium': return 'bg-amber-50 text-amber-700 border-amber-200';
            case 'low': return 'bg-green-50 text-green-700 border-green-200';
            default: return 'bg-gray-50 text-gray-700 border-gray-200';
        }
    };

    const getBadgeColor = (level) => {
        switch (level?.toLowerCase()) {
            case 'high': return 'bg-red-100 text-red-800';
            case 'medium': return 'bg-amber-100 text-amber-800';
            case 'low': return 'bg-green-100 text-green-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div className={`p-4 rounded-xl border ${getColor(riskLevel)} transition-all duration-200 hover:shadow-md`}>
            <div className="flex justify-between items-start mb-3">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${getBadgeColor(riskLevel)}`}>
                            {horizon || 'T+1'}
                        </span>
                        {riskLevel === 'high' && <AlertTriangle className="w-4 h-4 text-red-600 animate-pulse" />}
                    </div>
                    <h3 className="font-bold text-sm">{organism}</h3>
                    <p className="text-xs opacity-80">{antibiotic} in {ward}</p>
                </div>
                <div className="text-right">
                    <div className="text-2xl font-bold">{(probability * 100).toFixed(0)}%</div>
                    <div className="text-[10px] uppercase font-bold tracking-wider opacity-60">Resistance Prob</div>
                </div>
            </div>

            <div className="w-full bg-black/10 rounded-full h-1.5 mb-2 overflow-hidden">
                <div 
                    className={`h-full rounded-full transition-all duration-1000 ${riskLevel === 'high' ? 'bg-red-500' : riskLevel === 'medium' ? 'bg-amber-500' : 'bg-green-500'}`}
                    style={{ width: `${probability * 100}%` }}
                />
            </div>

            <div className="flex items-center justify-between text-xs opacity-70">
                <div className="flex items-center gap-1">
                    <HelpCircle className="w-3 h-3" />
                    <span>Uncertainty: ±{(uncertainty * 100).toFixed(1)}%</span>
                </div>
            </div>
        </div>
    );
};

export default RiskCard;
