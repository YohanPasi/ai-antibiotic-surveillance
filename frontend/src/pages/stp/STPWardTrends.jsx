import React, { useState, useEffect } from 'react';
import { BarChart2, Filter } from 'lucide-react';
import TrendChart from '../../components/stp/TrendChart';

const API = 'http://localhost:8000';

const ORGANISMS = [
    'Streptococcus pneumoniae',
    'Enterococcus faecalis',
    'Enterococcus faecium',
    'Streptococcus pyogenes',
    'E. coli',
    'K. pneumoniae',
    'P. aeruginosa',
    'S. aureus'
];

const getRiskColor = (rate) => {
    if (rate > 0.5) return { text: 'text-red-700', bg: 'bg-red-100 border-red-200', label: 'High Resistance' };
    if (rate > 0.2) return { text: 'text-amber-700', bg: 'bg-amber-100 border-amber-200', label: 'Moderate' };
    return { text: 'text-emerald-700', bg: 'bg-emerald-100 border-emerald-200', label: 'Low' };
};

const STPWardTrends = () => {
    const [selectedWard, setSelectedWard] = useState('ICU');
    const [selectedOrganism, setSelectedOrganism] = useState('Streptococcus pneumoniae');
    const [trendData, setTrendData] = useState([]);
    const [profileData, setProfileData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [wards, setWards] = useState([]);

    useEffect(() => {
        fetch(`${API}/api/stp/stage2/wards`)
            .then(r => r.ok ? r.json() : [])
            .then(data => {
                setWards(data.length > 0 ? data : ['ICU', 'General Ward', 'Surgical Ward']);
                if (data.length > 0 && !data.includes('ICU')) setSelectedWard(data[0]);
            })
            .catch(() => setWards(['ICU', 'General Ward', 'Surgical Ward']));
    }, []);

    useEffect(() => {
        if (!selectedWard) return;
        setLoading(true);
        setError(null);

        Promise.all([
            fetch(`${API}/api/stp/stage2/weekly-rates?ward=${encodeURIComponent(selectedWard)}&organism=${encodeURIComponent(selectedOrganism)}&limit=52`),
            fetch(`${API}/api/stp/stage2/ward-profile?ward=${encodeURIComponent(selectedWard)}`)
        ])
            .then(async ([trendRes, profileRes]) => {
                if (trendRes.ok) {
                    const json = await trendRes.json();
                    setTrendData(json.map(item => ({ date: item.week_start, resistance_rate: item.resistance_rate })).reverse());
                }
                if (profileRes.ok) setProfileData(await profileRes.json());
            })
            .catch(e => setError('Could not load ward data. Please try again.'))
            .finally(() => setLoading(false));
    }, [selectedWard, selectedOrganism]);

    return (
        <div className="space-y-6">
            {/* Header + Filters */}
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Ward Resistance Trends</h1>
                    <p className="text-sm text-slate-500 mt-0.5">Historical antibiotic resistance levels per ward and organism</p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 shadow-sm">
                        <Filter className="w-4 h-4 text-slate-400" />
                        <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Ward</label>
                        <select
                            value={selectedWard}
                            onChange={e => setSelectedWard(e.target.value)}
                            className="bg-transparent text-sm text-slate-700 dark:text-gray-200 outline-none cursor-pointer"
                        >
                            {wards.map(w => <option key={w} value={w}>{w}</option>)}
                        </select>
                    </div>
                    <div className="flex items-center gap-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 shadow-sm">
                        <BarChart2 className="w-4 h-4 text-slate-400" />
                        <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Organism</label>
                        <select
                            value={selectedOrganism}
                            onChange={e => setSelectedOrganism(e.target.value)}
                            className="bg-transparent text-sm text-slate-700 dark:text-gray-200 outline-none cursor-pointer"
                        >
                            {ORGANISMS.map(o => <option key={o} value={o}>{o}</option>)}
                        </select>
                    </div>
                </div>
            </div>

            {loading && (
                <div className="flex items-center justify-center h-40">
                    <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
                </div>
            )}

            {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">{error}</div>
            )}

            {!loading && !error && (
                <div className="space-y-6">
                    {/* Trend Chart */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
                        <div className="mb-4">
                            <h2 className="font-semibold text-slate-800 dark:text-white">12-Month Trend</h2>
                            <p className="text-sm text-slate-500">{selectedWard} · {selectedOrganism} — weekly resistance rate</p>
                        </div>
                        {trendData.length > 0
                            ? <TrendChart data={trendData} title="" />
                            : <div className="h-32 flex items-center justify-center text-slate-400 text-sm">No trend data available for this selection</div>}
                    </div>

                    {/* Profile Heatmap */}
                    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 shadow-sm p-6">
                        <div className="mb-4 flex items-center justify-between">
                            <div>
                                <h2 className="font-semibold text-slate-800 dark:text-white">Antibiotic Resistance Profile</h2>
                                <p className="text-sm text-slate-500">All organisms tested in {selectedWard}</p>
                            </div>
                            <div className="flex gap-3 text-xs text-slate-500">
                                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-400 inline-block" /> High (&gt;50%)</span>
                                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-amber-400 inline-block" /> Moderate</span>
                                <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-emerald-400 inline-block" /> Low</span>
                            </div>
                        </div>

                        {profileData.length === 0 ? (
                            <div className="py-10 text-center text-slate-400 text-sm">No profile data for this ward</div>
                        ) : (
                            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                                {profileData.map((item, idx) => {
                                    const risk = getRiskColor(item.mean_resistance);
                                    return (
                                        <div key={idx} className={`rounded-xl border p-3 ${risk.bg}`}>
                                            <p className="text-xs text-slate-500 leading-tight mb-1">{item.organism}</p>
                                            <p className="font-bold text-sm text-slate-700 dark:text-gray-200 truncate" title={item.antibiotic}>{item.antibiotic}</p>
                                            <div className="mt-2 flex items-center justify-between">
                                                <span className={`text-lg font-black ${risk.text}`}>{(item.mean_resistance * 100).toFixed(0)}%</span>
                                                <span className={`text-xs font-semibold ${risk.text}`}>{risk.label}</span>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default STPWardTrends;
