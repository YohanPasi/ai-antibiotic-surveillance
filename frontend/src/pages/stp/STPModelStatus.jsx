
import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

const STPModelStatus = () => {
    const [modelStatus, setModelStatus] = useState({ models: [], disclaimer: '' });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchModelStatus();
    }, []);

    const fetchModelStatus = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/stp/feedback/model-status');
            if (response.ok) {
                const data = await response.json();
                setModelStatus(data);
            }
        } catch (error) {
            console.error('Failed to fetch model status:', error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (status) => {
        const colors = {
            'active': 'bg-green-100 text-green-800 border-green-300',
            'shadow': 'bg-blue-100 text-blue-800 border-blue-300',
            'staging': 'bg-amber-100 text-amber-800 border-amber-300',
            'archived': 'bg-gray-100 text-gray-800 border-gray-300'
        };
        return colors[status] || colors['active'];
    };

    const getPassRateColor = (passRate) => {
        if (passRate >= 0.8) return 'text-green-600';
        if (passRate >= 0.6) return 'text-amber-600';
        return 'text-red-600';
    };

    return (
        <div className="space-y-6">
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <p className="text-sm text-purple-800 font-medium">
                    {modelStatus.disclaimer}
                </p>
            </div>

            {loading ? (
                <div className="text-center py-12 text-gray-500">Loading model status...</div>
            ) : (
                <div className="grid gap-6">
                    {modelStatus.models.map((model) => (
                        <div key={model.model_id} className="border-2 rounded-lg p-6 bg-white shadow-sm hover:shadow-md transition">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <h3 className="text-lg font-semibold mb-2">{model.type}</h3>
                                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${getStatusBadge(model.status)}`}>
                                        {model.status.toUpperCase()}
                                    </span>
                                </div>
                                <Activity className="text-purple-600" size={28} />
                            </div>

                            <div className="grid grid-cols-3 gap-6 mt-6">
                                <div className="flex items-start gap-3">
                                    <div className="p-2 bg-blue-100 rounded-lg">
                                        <TrendingUp className="text-blue-600" size={20} />
                                    </div>
                                    <div>
                                        <div className="text-2xl font-bold">{model.validations}</div>
                                        <div className="text-sm text-gray-600">Validations</div>
                                    </div>
                                </div>

                                <div className="flex items-start gap-3">
                                    <div className="p-2 bg-green-100 rounded-lg">
                                        <CheckCircle className="text-green-600" size={20} />
                                    </div>
                                    <div>
                                        <div className={`text-2xl font-bold ${getPassRateColor(model.pass_rate)}`}>
                                            {(model.pass_rate * 100).toFixed(0)}%
                                        </div>
                                        <div className="text-sm text-gray-600">CI Pass Rate</div>
                                    </div>
                                </div>

                                <div className="flex items-start gap-3">
                                    <div className="p-2 bg-amber-100 rounded-lg">
                                        <AlertCircle className="text-amber-600" size={20} />
                                    </div>
                                    <div>
                                        <div className="text-2xl font-bold">{(model.avg_error * 100).toFixed(1)}%</div>
                                        <div className="text-sm text-gray-600">Avg Absolute Error</div>
                                    </div>
                                </div>
                            </div>

                            {model.validations > 0 && (
                                <div className="mt-4 pt-4 border-t">
                                    <div className="text-xs text-gray-600">
                                        {model.pass_rate < 0.7 && (
                                            <div className="flex items-center gap-2 text-amber-700">
                                                <AlertCircle size={16} />
                                                <span>Performance below threshold - retraining may be warranted</span>
                                            </div>
                                        )}
                                        {model.pass_rate >= 0.8 && (
                                            <div className="flex items-center gap-2 text-green-700">
                                                <CheckCircle size={16} />
                                                <span>Model performing within expected range</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}

                    {modelStatus.models.length === 0 && (
                        <div className="text-center py-12 text-gray-500">
                            No models found. Deploy models to see status here.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default STPModelStatus;
