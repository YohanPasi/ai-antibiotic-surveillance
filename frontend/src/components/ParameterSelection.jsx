export default function ParameterSelection({ options, selectedParams, onChange, loading }) {
    const handleChange = (field, value) => {
        onChange({ ...selectedParams, [field]: value || null })
    }

    return (
        <div className="card">
            <h2 className="text-2xl font-semibold text-primary-400 mb-6">
                📋 Select Parameters
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Organism Selection */}
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                        Organism *
                    </label>
                    <select
                        value={selectedParams.organism}
                        onChange={(e) => handleChange('organism', e.target.value)}
                        className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                        disabled={loading}
                    >
                        <option value="">Select organism...</option>
                        {options.organisms.map((org) => (
                            <option key={org} value={org}>{org}</option>
                        ))}
                    </select>
                </div>

                {/* Antibiotic Selection */}
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                        Antibiotic *
                    </label>
                    <select
                        value={selectedParams.antibiotic}
                        onChange={(e) => handleChange('antibiotic', e.target.value)}
                        className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                        disabled={loading}
                    >
                        <option value="">Select antibiotic...</option>
                        {options.antibiotics.map((ab) => (
                            <option key={ab} value={ab}>{ab}</option>
                        ))}
                    </select>
                </div>

                {/* Ward Selection (Optional) */}
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                        Ward (Optional)
                    </label>
                    <select
                        value={selectedParams.ward || ''}
                        onChange={(e) => handleChange('ward', e.target.value)}
                        className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-3 text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                        disabled={loading}
                    >
                        <option value="">Organism-level (All wards)</option>
                        {options.wards.map((ward) => (
                            <option key={ward} value={ward}>{ward}</option>
                        ))}
                    </select>
                </div>
            </div>

            {loading && (
                <div className="mt-4 text-center">
                    <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500"></div>
                    <span className="ml-3 text-gray-400">Loading data...</span>
                </div>
            )}
        </div>
    )
}
