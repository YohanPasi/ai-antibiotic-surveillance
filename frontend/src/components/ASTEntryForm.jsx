import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle, CheckCircle, Plus, Trash2, Beaker } from 'lucide-react';

// Default Panels per Organism
const DRUG_PANELS = {
    'Pseudomonas aeruginosa': ['Meropenem (MEM)', 'Ceftazidime (CAZ)', 'Ciprofloxacin (CIP)', 'Amikacin (AK)', 'Piperacillin-Tazobactam (TZP)'],
    'Acinetobacter spp.': ['Meropenem (MEM)', 'Imipenem (IPM)', 'Ampicillin-Sulbactam (SAM)', 'Ciprofloxacin (CIP)', 'Gentamicin (CN)'],
    'Escherichia coli': ['Ampicillin (AMP)', 'Cefuroxime (CXM)', 'Ceftriaxone (CRO)', 'Gentamicin (CN)', 'Imipenem (IPM)'],
    'Klebsiella pneumoniae': ['Amoxicillin-Clavulanate (AMC)', 'Ceftazidime (CAZ)', 'Ciprofloxacin (CIP)', 'Meropenem (MEM)']
};

const ASTEntryForm = ({ isOpen, onClose, onEntrySaved }) => {
    // Metadata State
    const [metadata, setMetadata] = useState({
        ward: 'ICU',
        organism: 'Pseudomonas aeruginosa',
        specimen_type: 'Urine',
        lab_no: '',
        age: '',
        gender: 'Male',
        bht: ''
    });

    // Panel State: [{ id, antibiotic, result: '' }]
    const [panel, setPanel] = useState([]);
    const [newDrug, setNewDrug] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState(null);

    // Auto-Populate Panel on Organism Change
    useEffect(() => {
        const defaults = DRUG_PANELS[metadata.organism] || [];
        setPanel(defaults.map((drug, idx) => ({ id: idx, antibiotic: drug, result: '' })));
    }, [metadata.organism]);

    if (!isOpen) return null;

    const handleMetaChange = (e) => {
        const { name, value } = e.target;
        setMetadata(prev => ({ ...prev, [name]: value }));
    };

    const handleResultChange = (id, res) => {
        setPanel(prev => prev.map(item => item.id === id ? { ...item, result: res } : item));
    };

    const addCustomDrug = () => {
        if (!newDrug.trim()) return;
        setPanel(prev => [...prev, { id: Date.now(), antibiotic: newDrug, result: '' }]);
        setNewDrug('');
    };

    const removeDrug = (id) => {
        setPanel(prev => prev.filter(item => item.id !== id));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage(null);

        // Filter out incomplete rows
        const validResults = panel.filter(p => p.result !== '').map(p => ({
            antibiotic: p.antibiotic,
            result: p.result
        }));

        if (validResults.length === 0) {
            setMessage({ type: 'error', text: 'Please enter at least one antibiotic result' });
            setLoading(false);
            return;
        }

        const payload = {
            ...metadata,
            results: validResults
        };

        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/api/entry`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (response.ok) {
                setMessage({ type: 'success', text: data.message });
                setTimeout(() => {
                    onClose();
                    if (onEntrySaved) onEntrySaved();
                }, 1500);
            } else {
                setMessage({ type: 'error', text: data.detail || 'Failed to save entry' });
            }
        } catch (error) {
            setMessage({ type: 'error', text: 'Network Error' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80 backdrop-blur-sm">
            <div className="bg-gray-900 border border-gray-700 rounded-lg w-[800px] h-[90vh] flex flex-col shadow-2xl overflow-hidden">
                {/* Header */}
                <div className="flex justify-between items-center p-5 border-b border-gray-800 bg-gray-800/50">
                    <div>
                        <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
                            <Beaker className="w-5 h-5 text-purple-400" />
                            Clinical Isolate Entry
                        </h2>
                        <p className="text-xs text-gray-400">Enter full susceptibility panel for a single isolate</p>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white"><X className="w-6 h-6" /></button>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {/* Metadata Section */}
                    <div className="grid grid-cols-3 gap-4 bg-gray-800/30 p-4 rounded-lg border border-gray-800">
                        <div>
                            <label className="block text-xs text-gray-400 mb-1">Ward</label>
                            <select name="ward" value={metadata.ward} onChange={handleMetaChange} className="w-full form-select bg-gray-800 border-gray-700 rounded text-sm text-gray-200">
                                <option>ICU</option><option>Ward 02</option><option>Ward 05</option><option>A&E</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs text-gray-400 mb-1">Specimen</label>
                            <select name="specimen_type" value={metadata.specimen_type} onChange={handleMetaChange} className="w-full form-select bg-gray-800 border-gray-700 rounded text-sm text-gray-200">
                                <option>Urine</option><option>Blood</option><option>Pus</option><option>ET Tube</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs text-gray-400 mb-1">Organism</label>
                            <select name="organism" value={metadata.organism} onChange={handleMetaChange} className="w-full form-select bg-gray-800 border-blue-900/50 rounded text-sm text-blue-200 font-bold">
                                <option>Pseudomonas aeruginosa</option>
                                <option>Acinetobacter spp.</option>
                                <option>Escherichia coli</option>
                                <option>Klebsiella pneumoniae</option>
                            </select>
                        </div>
                        <input type="text" name="lab_no" placeholder="Lab No" onChange={handleMetaChange} className="bg-gray-800 border-gray-700 rounded p-2 text-sm text-gray-300" />
                        <input type="text" name="bht" placeholder="BHT" onChange={handleMetaChange} className="bg-gray-800 border-gray-700 rounded p-2 text-sm text-gray-300" />
                        <div className="flex gap-2">
                            <input type="number" name="age" placeholder="Age" onChange={handleMetaChange} className="w-20 bg-gray-800 border-gray-700 rounded p-2 text-sm text-gray-300" />
                            <select name="gender" onChange={handleMetaChange} className="flex-1 bg-gray-800 border-gray-700 rounded text-sm text-gray-300">
                                <option>Male</option><option>Female</option>
                            </select>
                        </div>
                    </div>

                    {/* Antibiogram Panel */}
                    <div>
                        <div className="flex justify-between items-end mb-2">
                            <h3 className="text-sm font-bold text-gray-300">Antibiogram Results</h3>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    placeholder="Add Custom Antibiotic..."
                                    value={newDrug}
                                    onChange={(e) => setNewDrug(e.target.value)}
                                    className="bg-gray-800 border-gray-700 rounded px-2 py-1 text-xs w-48 text-white focus:border-blue-500"
                                    onKeyDown={(e) => e.key === 'Enter' && addCustomDrug()}
                                />
                                <button onClick={addCustomDrug} className="bg-gray-700 hover:bg-gray-600 text-white px-2 py-1 rounded text-xs flex items-center">
                                    <Plus className="w-3 h-3 mr-1" /> Add
                                </button>
                            </div>
                        </div>

                        <div className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-gray-800 text-gray-400 uppercase text-xs">
                                    <tr>
                                        <th className="px-4 py-3">Antibiotic</th>
                                        <th className="px-4 py-3 text-center">Result (S / I / R)</th>
                                        <th className="px-4 py-3 w-10"></th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-800">
                                    {panel.map((row) => (
                                        <tr key={row.id} className="hover:bg-gray-800/30">
                                            <td className="px-4 py-2 font-mono text-gray-300">{row.antibiotic}</td>
                                            <td className="px-4 py-2 flex justify-center gap-2">
                                                {['S', 'I', 'R'].map(opt => (
                                                    <button
                                                        key={opt}
                                                        type="button"
                                                        onClick={() => handleResultChange(row.id, opt)}
                                                        className={`w-8 h-8 rounded-full font-bold text-xs transition-colors border ${row.result === opt
                                                                ? (opt === 'S' ? 'bg-green-600 border-green-400 text-white' : opt === 'R' ? 'bg-red-600 border-red-400 text-white' : 'bg-yellow-600 border-yellow-400 text-white')
                                                                : 'bg-gray-800 border-gray-700 text-gray-500 hover:border-gray-500'
                                                            }`}
                                                    >
                                                        {opt}
                                                    </button>
                                                ))}
                                            </td>
                                            <td className="px-4 py-2 text-center">
                                                <button onClick={() => removeDrug(row.id)} className="text-gray-600 hover:text-red-400">
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                    {panel.length === 0 && (
                                        <tr><td colSpan="3" className="p-8 text-center text-gray-500 italic">No antibiotics selected for this panel.</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-5 border-t border-gray-800 bg-gray-800/50 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        {message && (
                            <div className={`px-3 py-1 rounded flex items-center gap-2 text-xs ${message.type === 'success' ? 'bg-green-900/30 text-green-300 border border-green-800' : 'bg-red-900/30 text-red-300 border border-red-800'
                                }`}>
                                {message.type === 'success' ? <CheckCircle className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                                {message.text}
                            </div>
                        )}
                    </div>
                    <div className="flex gap-3">
                        <button type="button" onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-white text-sm">Cancel</button>
                        <button
                            onClick={handleSubmit}
                            disabled={loading}
                            className="bg-purple-600 hover:bg-purple-500 text-white px-6 py-2 rounded font-bold shadow-lg shadow-purple-900/20 flex items-center gap-2 disabled:opacity-50"
                        >
                            <Save className="w-4 h-4" />
                            {loading ? 'Processing Pipeline...' : 'Commit Panel & Predict'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ASTEntryForm;
