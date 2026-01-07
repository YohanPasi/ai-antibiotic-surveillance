
import React from 'react';
import RiskCard from '../../components/stp/RiskCard';
import SHAPSummary from '../../components/stp/SHAPSummary';
import { Shield } from 'lucide-react';

const STPEarlyWarning = () => {
    // Mock Data
    const predictions = [
        {
            ward: 'ICU', organism: 'E. coli', antibiotic: 'Meropenem',
            prediction: { probability: 0.85, risk: 'high', uncertainty: 0.05, horizon: 'T+1' },
            features: [
                { name: 'Prev Ward Prevalence', value: 0.23 },
                { name: 'Days since admission', value: 0.12 },
                { name: 'Recent Cephalosporin', value: 0.08 },
                { name: 'Age < 50', value: -0.05 }
            ]
        },
        {
            ward: 'General Ward A', organism: 'K. pneumoniae', antibiotic: 'Ciprofloxacin',
            prediction: { probability: 0.45, risk: 'medium', uncertainty: 0.12, horizon: 'T+2' },
            features: [
                { name: 'Prev Colonization', value: 0.15 },
                { name: 'Transfer from ICU', value: 0.09 },
            ]
        }
    ];

    return (
        <div className="space-y-6">
            <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-lg mb-6">
                <div className="flex gap-3">
                    <Shield className="w-5 h-5 text-amber-500" />
                    <p className="text-sm text-amber-800 font-medium">
                        ⚠ Early warning for epidemiological surveillance only.
                    </p>
                </div>
            </div>

            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-slate-800 dark:text-white">Early Warning (AI)</h2>
                <div className="flex gap-2">
                    <span className="px-3 py-1 bg-gray-100 rounded-full text-xs font-bold text-gray-600">Horizon: T+1 Week</span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {predictions.map((pred, idx) => (
                    <div key={idx} className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm hover:shadow-lg transition-shadow">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <h3 className="font-bold text-gray-400 text-xs uppercase tracking-wider mb-2">Risk Assessment</h3>
                                <RiskCard
                                    ward={pred.ward}
                                    organism={pred.organism}
                                    antibiotic={pred.antibiotic}
                                    probability={pred.prediction.probability}
                                    riskLevel={pred.prediction.risk}
                                    uncertainty={pred.prediction.uncertainty}
                                    horizon={pred.prediction.horizon}
                                />
                            </div>
                            <div>
                                <h3 className="font-bold text-gray-400 text-xs uppercase tracking-wider mb-2">Driver Analysis</h3>
                                <SHAPSummary features={pred.features} />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default STPEarlyWarning;
