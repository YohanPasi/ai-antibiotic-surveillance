
import React, { useState, useEffect } from 'react';
import TrendChart from '../../components/stp/TrendChart';
import { useAuth } from '../../context/AuthContext';

const STPWardTrends = () => {
    const { token } = useAuth();
    const [selectedWard, setSelectedWard] = useState('ICU');
    const [selectedOrganism, setSelectedOrganism] = useState('Streptococcus pneumoniae'); // STP Default
    const [trendData, setTrendData] = useState([]);
    const [profileData, setProfileData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const wards = ['ICU', 'General Ward', 'Surgical Ward'];
    const organisms = [
        'Streptococcus pneumoniae',
        'Enterococcus faecalis',
        'Enterococcus faecium',
        'Streptococcus pyogenes',
        'E. coli',
        'K. pneumoniae',
        'P. aeruginosa',
        'S. aureus'
    ];

    useEffect(() => {
        const fetchData = async () => {
            if (!token) return;
            setLoading(true);
            setError(null);
            try {
                const headers = { 'Authorization': `Bearer ${token}` };

                // 1. Fetch Weekly Trends
                const trendRes = await fetch(`${import.meta.env.VITE_API_URL}/api/stp/stage2/weekly-rates?ward=${selectedWard}&organism=${encodeURIComponent(selectedOrganism)}&limit=52`, { headers });
                if (!trendRes.ok) throw new Error('Failed to fetch trends');
                const trendJson = await trendRes.json();

                const formattedTrends = trendJson.map(item => ({
                    date: item.week_start,
                    resistance_rate: item.resistance_rate
                })).reverse();

                setTrendData(formattedTrends);

                // 2. Fetch Ward Profile (Heatmap Data)
                const profileRes = await fetch(`${import.meta.env.VITE_API_URL}/api/stp/stage2/ward-profile?ward=${selectedWard}`, { headers });
                if (!profileRes.ok) throw new Error('Failed to fetch profile');
                const profileJson = await profileRes.json();
                setProfileData(profileJson);

            } catch (err) {
                console.error(err);
                setError(err.message);
                setTrendData([]);
                setProfileData([]);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [selectedWard, selectedOrganism, token]);

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800 dark:text-white">Ward Resistance Trends</h2>
                    <p className="text-slate-500">Descriptive Surveillance (Real-time DB Data)</p>
                </div>

                {/* Selectors */}
                <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center gap-2">
                        <label className="text-sm font-medium text-slate-600 dark:text-gray-400">Ward:</label>
                        <select
                            value={selectedWard}
                            onChange={(e) => setSelectedWard(e.target.value)}
                            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                        >
                            {wards.map(w => <option key={w} value={w}>{w}</option>)}
                        </select>
                    </div>

                    <div className="flex items-center gap-2">
                        <label className="text-sm font-medium text-slate-600 dark:text-gray-400">Organism:</label>
                        <select
                            value={selectedOrganism}
                            onChange={(e) => setSelectedOrganism(e.target.value)}
                            className="px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                        >
                            {organisms.map(o => <option key={o} value={o}>{o}</option>)}
                        </select>
                    </div>
                </div>
            </div>

            {loading && <div className="text-center py-10 text-slate-400 animate-pulse">Loading data for {selectedWard} / {selectedOrganism}...</div>}

            {error && <div className="text-center py-10 text-red-400">Error loading data: {error}</div>}

            {!loading && !error && (
                <div className="grid grid-cols-1 gap-6">
                    {/* Trend Chart */}
                    <TrendChart
                        data={trendData}
                        title={`${selectedWard}: ${selectedOrganism} Resistance`}
                    />

                    {/* Heatmap Visualization */}
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm">
                        <div className="flex justify-between items-center mb-4">
                            <h4 className="text-sm font-bold text-slate-700 dark:text-gray-200">Ward Resistance Profile</h4>
                            <span className="text-xs text-slate-400">Data Range: 2024-01-01 to 2025-12-31 | All Organisms in {selectedWard}</span>
                        </div>

                        {profileData.length === 0 ? (
                            <div className="h-64 flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900 rounded-lg text-slate-400">
                                <p>No specific profile data found for {selectedWard}.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                                {profileData.map((item, idx) => (
                                    <div key={idx} className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-100 dark:border-gray-800">
                                        <div className="text-xs text-slate-500 mb-1">{item.organism}</div>
                                        <div className="font-bold text-sm text-slate-700 dark:text-gray-300 truncate" title={item.antibiotic}>{item.antibiotic}</div>
                                        <div className="mt-2 text-right">
                                            <span
                                                className={`text-xs font-bold px-2 py-1 rounded 
                                                ${item.mean_resistance > 0.5 ? 'bg-red-100 text-red-700' :
                                                        item.mean_resistance > 0.2 ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}`}
                                            >
                                                {(item.mean_resistance * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default STPWardTrends;
