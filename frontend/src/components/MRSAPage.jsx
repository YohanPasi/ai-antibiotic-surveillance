import React, { useState } from 'react';
import MRSAResultPanel from './MRSAResultPanel';
import MRSAValidationLog from './MRSAValidationLog';

const MRSAPage = () => {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Master Data State
    const [wardOptions, setWardOptions] = useState([]);
    const [sampleOptions, setSampleOptions] = useState([]);

    const [formData, setFormData] = useState({
        age: 65,
        gender: "Male",
        ward: "", // Wait for load
        sample_type: "Blood",
        pus_type: "Unknown",
        cell_count: 0,
        gram_positivity: "GPC",
        growth_time: 24.0,
        bht: "Unknown"
    });

    // Fetch Master Data
    React.useEffect(() => {
        const fetchMasterData = async () => {
            try {
                // Fetch Wards
                const wardRes = await fetch('http://localhost:8000/api/master/definitions/WARD');
                if (wardRes.ok) {
                    const wards = await wardRes.json();
                    setWardOptions(wards);
                    // Set default if empty
                    if (wards.length > 0) {
                        setFormData(prev => ({ ...prev, ward: wards[0].value }));
                    }
                }

                // Fetch Sample Types
                const sampleRes = await fetch('http://localhost:8000/api/master/definitions/SAMPLE_TYPE');
                if (sampleRes.ok) {
                    const samples = await sampleRes.json();
                    setSampleOptions(samples);
                }
            } catch (err) {
                console.error("Failed to load master data", err);
            }
        };

        fetchMasterData();
    }, []);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const token = localStorage.getItem('token');
            const response = await fetch('http://localhost:8000/api/mrsa/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "Prediction failed");
            }

            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-900 text-slate-100 p-8 pt-20 font-sans">
            {/* Background Effects */}
            <div className="fixed inset-0 z-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-800 via-slate-900 to-black opacity-80 pointer-events-none"></div>

            <div className="relative z-10 max-w-5xl mx-auto">
                <header className="mb-10 text-center space-y-2">
                    <h1 className="text-5xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400 tracking-tight">
                        MRSA Risk Intelligence
                    </h1>
                    <p className="text-slate-400 text-lg max-w-2xl mx-auto">
                        Advanced AI-driven pre-AST screening for Staphylococcus aureus.
                    </p>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    {/* Left: Input Form */}
                    <div className="lg:col-span-5">
                        <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-2xl relative overflow-hidden group">
                            <div className="absolute inset-0 bg-gradient-to-b from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

                            <h2 className="text-2xl font-bold mb-6 flex items-center gap-3 text-white">
                                <span className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-sm">1</span>
                                Clinical Data
                            </h2>

                            <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
                                <div className="grid grid-cols-2 gap-5">
                                    <div className="space-y-1">
                                        <label className="text-xs uppercase tracking-wider font-semibold text-slate-400 pl-1">Age</label>
                                        <input type="number" name="age" value={formData.age} onChange={handleChange}
                                            className="w-full bg-slate-800/50 border border-slate-700/50 text-white rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all placeholder-slate-600" required />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs uppercase tracking-wider font-semibold text-slate-400 pl-1">Gender</label>
                                        <select name="gender" value={formData.gender} onChange={handleChange}
                                            className="w-full bg-slate-800/50 border border-slate-700/50 text-white rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none appearance-none">
                                            <option>Male</option>
                                            <option>Female</option>
                                            <option>Unknown</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs uppercase tracking-wider font-semibold text-slate-400 pl-1">Hospital Ward</label>
                                    <select name="ward" value={formData.ward} onChange={handleChange}
                                        className="w-full bg-slate-800/50 border border-slate-700/50 text-white rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none">
                                        {wardOptions.length === 0 && <option>Loading...</option>}
                                        {wardOptions.map(opt => (
                                            <option key={opt.id} value={opt.value}>{opt.label}</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="grid grid-cols-2 gap-5">
                                    <div className="space-y-1">
                                        <label className="text-xs uppercase tracking-wider font-semibold text-slate-400 pl-1">Sample Type</label>
                                        <select name="sample_type" value={formData.sample_type} onChange={handleChange}
                                            className="w-full bg-slate-800/50 border border-slate-700/50 text-white rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none">
                                            {sampleOptions.length === 0 && <option>Loading...</option>}
                                            {sampleOptions.map(opt => (
                                                <option key={opt.id} value={opt.value}>{opt.label}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs uppercase tracking-wider font-semibold text-slate-400 pl-1">Growth (hrs)</label>
                                        <input type="number" name="growth_time" value={formData.growth_time} onChange={handleChange}
                                            className="w-full bg-slate-800/50 border border-slate-700/50 text-white rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none transition-all" step="0.5" />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-5">
                                    <div className="space-y-1">
                                        <label className="text-xs uppercase tracking-wider font-semibold text-slate-400 pl-1">Gram Stain</label>
                                        <select name="gram_positivity" value={formData.gram_positivity} onChange={handleChange}
                                            className="w-full bg-slate-800/50 border border-slate-700/50 text-white rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none">
                                            <option value="GPC">GPC (Cocci)</option>
                                            <option value="Unknown">Unknown</option>
                                        </select>
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs uppercase tracking-wider font-semibold text-slate-400 pl-1">Cell Count</label>
                                        <input type="number" name="cell_count" value={formData.cell_count} onChange={handleChange}
                                            className="w-full bg-slate-800/50 border border-slate-700/50 text-white rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none transition-all" min="0" max="4" />
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <label className="text-xs uppercase tracking-wider font-semibold text-slate-400 pl-1">Patient ID / BHT (Optional)</label>
                                    <input type="text" name="bht" value={formData.bht} onChange={handleChange}
                                        className="w-full bg-slate-800/50 border border-slate-700/50 text-white rounded-xl px-4 py-3 focus:ring-2 focus:ring-blue-500 outline-none transition-all placeholder-slate-600" placeholder="For audit logs" />
                                </div>

                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full py-4 mt-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold rounded-xl shadow-lg shadow-blue-900/40 transition-all transform active:scale-[0.98] flex justify-center items-center gap-2 group-disabled:opacity-70 group-disabled:cursor-not-allowed"
                                >
                                    {loading ? (
                                        <>
                                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                            <span>Processing...</span>
                                        </>
                                    ) : (
                                        <>
                                            <span>Run Risk Assessment</span>
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                                        </>
                                    )}
                                </button>
                            </form>
                            {error && (
                                <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 text-red-200 rounded-xl text-sm flex items-start gap-3 backdrop-blur-md">
                                    <svg className="w-5 h-5 min-w-[20px] text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                    {error}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Right: Result Panel */}
                    <div className="lg:col-span-7">
                        <div className="h-full">
                            <MRSAResultPanel prediction={result} loading={loading} />
                        </div>
                    </div>
                </div>
            </div>

            {/* Stage D: Validation History */}
            <div className="mt-12 mb-8">
                <MRSAValidationLog />
            </div>
        </div>
    );
};

export default MRSAPage;
