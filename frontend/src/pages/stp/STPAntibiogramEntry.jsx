
import React, { useState } from 'react';
import { Plus, Trash2, Save, AlertCircle } from 'lucide-react';

const STPAntibiogramEntry = () => {
    const [formData, setFormData] = useState({
        ward: '',
        organism: '',
        sample_date: '',
        data_source: 'MANUAL',
        isolates: [[]]
    });
    const [acknowledged, setAcknowledged] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    const antibiotics = [
        'Ceftriaxone', 'Ciprofloxacin', 'Meropenem', 'Amikacin',
        'Vancomycin', 'Linezolid', 'Gentamicin', 'Ampicillin',
        'Piperacillin-Tazobactam', 'Cefepime'
    ];

    const wards = ['ICU', 'Surgical Ward A', 'Surgical Ward B', 'Surgical Ward C', 'Medical Ward A', 'Medical Ward B', 'Burn Unit'];
    const organisms = [
        'Escherichia coli', 'Klebsiella pneumoniae', 'Pseudomonas aeruginosa',
        'Staphylococcus aureus', 'Enterococcus faecalis', 'Enterococcus faecium',
        'Acinetobacter baumannii'
    ];

    const addIsolate = () => {
        setFormData(prev => ({
            ...prev,
            isolates: [...prev.isolates, []]
        }));
    };

    const removeIsolate = (idx) => {
        setFormData(prev => ({
            ...prev,
            isolates: prev.isolates.filter((_, i) => i !== idx)
        }));
    };

    const updateAST = (isolateIdx, antibiotic, result) => {
        const newIsolates = [...formData.isolates];
        const isolate = newIsolates[isolateIdx];

        const astIdx = isolate.findIndex(a => a.antibiotic === antibiotic);
        if (astIdx >= 0) {
            isolate[astIdx].result = result;
        } else {
            isolate.push({ antibiotic, result });
        }

        setFormData(prev => ({ ...prev, isolates: newIsolates }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);

        try {
            const response = await fetch('http://localhost:8000/api/stp/feedback/antibiogram', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                alert(`Success! ${data.inserted} isolates inserted. ${data.duplicates_rejected} duplicates rejected.`);
                // Reset form
                setFormData({
                    ward: '',
                    organism: '',
                    sample_date: '',
                    data_source: 'MANUAL',
                    isolates: [[]]
                });
                setAcknowledged(false);
            } else {
                alert(`Error: ${data.detail || 'Submission failed'}`);
            }
        } catch (error) {
            console.error('Failed to submit:', error);
            alert('Network error. Please try again.');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* FIX #6: Safety Acknowledgment */}
            <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4">
                <label className="flex items-start gap-3 cursor-pointer">
                    <input
                        type="checkbox"
                        checked={acknowledged}
                        onChange={(e) => setAcknowledged(e.target.checked)}
                        className="mt-1 w-5 h-5"
                        required
                    />
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                            <AlertCircle className="text-red-600" size={20} />
                            <span className="font-bold text-red-900">Required Acknowledgment</span>
                        </div>
                        <span className="text-sm text-red-800">
                            I understand this system is for <strong>surveillance only</strong> and{' '}
                            <strong>NOT for patient treatment decisions</strong>. Data entered here supports
                            epidemiological monitoring and model validation.
                        </span>
                    </div>
                </label>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                    📊 <strong>Data Entry Guide:</strong> Enter individual isolate results (S/I/R/NA).
                    The system will automatically calculate resistance rates using validated algorithms.
                </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Metadata */}
                <div className="grid grid-cols-4 gap-4">
                    <div>
                        <label className="block text-sm font-medium mb-2">Ward *</label>
                        <select
                            value={formData.ward}
                            onChange={(e) => setFormData(prev => ({ ...prev, ward: e.target.value }))}
                            className="w-full border rounded px-3 py-2"
                            required
                        >
                            <option value="">Select Ward</option>
                            {wards.map(w => <option key={w} value={w}>{w}</option>)}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-2">Organism *</label>
                        <select
                            value={formData.organism}
                            onChange={(e) => setFormData(prev => ({ ...prev, organism: e.target.value }))}
                            className="w-full border rounded px-3 py-2"
                            required
                        >
                            <option value="">Select Organism</option>
                            {organisms.map(o => <option key={o} value={o}>{o}</option>)}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-2">Sample Date *</label>
                        <input
                            type="date"
                            value={formData.sample_date}
                            onChange={(e) => setFormData(prev => ({ ...prev, sample_date: e.target.value }))}
                            className="w-full border rounded px-3 py-2"
                            max={new Date().toISOString().split('T')[0]}
                            required
                        />
                    </div>

                    {/* FIX #2: Data Source */}
                    <div>
                        <label className="block text-sm font-medium mb-2">Data Source</label>
                        <select
                            value={formData.data_source}
                            onChange={(e) => setFormData(prev => ({ ...prev, data_source: e.target.value }))}
                            className="w-full border rounded px-3 py-2"
                        >
                            <option value="MANUAL">Manual Entry</option>
                            <option value="LIS">LIS Export</option>
                        </select>
                    </div>
                </div>

                {/* Isolates Grid */}
                <div className="space-y-4">
                    <div className="flex justify-between items-center">
                        <h3 className="text-lg font-semibold">Isolates ({formData.isolates.length})</h3>
                        <button
                            type="button"
                            onClick={addIsolate}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                            <Plus size={16} /> Add Isolate
                        </button>
                    </div>

                    {formData.isolates.map((isolate, idx) => (
                        <div key={idx} className="border rounded-lg p-4 bg-gray-50">
                            <div className="flex justify-between items-center mb-3">
                                <h4 className="font-medium">Isolate {idx + 1}</h4>
                                {idx > 0 && (
                                    <button
                                        type="button"
                                        onClick={() => removeIsolate(idx)}
                                        className="text-red-600 hover:text-red-800 flex items-center gap-1"
                                    >
                                        <Trash2 size={16} /> Remove
                                    </button>
                                )}
                            </div>

                            <div className="grid grid-cols-5 gap-3">
                                {antibiotics.map(antibiotic => {
                                    const ast = isolate.find(a => a.antibiotic === antibiotic);
                                    return (
                                        <div key={antibiotic}>
                                            <label className="block text-xs font-medium mb-1">{antibiotic}</label>
                                            <div className="flex gap-1">
                                                {['S', 'I', 'R', 'NA'].map(result => (
                                                    <button
                                                        key={result}
                                                        type="button"
                                                        onClick={() => updateAST(idx, antibiotic, result)}
                                                        className={`flex-1 px-1 py-1 text-xs rounded border ${ast?.result === result
                                                                ? result === 'S' ? 'bg-green-600 text-white border-green-600' :
                                                                    result === 'I' ? 'bg-yellow-600 text-white border-yellow-600' :
                                                                        result === 'R' ? 'bg-red-600 text-white border-red-600' :
                                                                            'bg-gray-600 text-white border-gray-600'
                                                                : 'bg-white hover:bg-gray-100'
                                                            }`}
                                                    >
                                                        {result}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>

                <button
                    type="submit"
                    disabled={!acknowledged || submitting}
                    className={`w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-medium transition ${acknowledged && !submitting
                            ? 'bg-green-600 text-white hover:bg-green-700'
                            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        }`}
                >
                    <Save size={20} /> {submitting ? 'Submitting...' : 'Submit Antibiogram'}
                </button>

                {!acknowledged && (
                    <p className="text-sm text-red-600 text-center">
                        ⚠️ Please acknowledge the surveillance-only disclaimer to submit
                    </p>
                )}
            </form>
        </div>
    );
};

export default STPAntibiogramEntry;
