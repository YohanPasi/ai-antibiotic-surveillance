import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Database, AlertCircle, Save } from 'lucide-react';

const MasterDataManager = () => {
    const [category, setCategory] = useState("WARD"); // WARD or SAMPLE_TYPE
    const [items, setItems] = useState([]);
    const [newItem, setNewItem] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Fetch Items
    useEffect(() => {
        fetchItems();
    }, [category]);

    const fetchItems = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/api/master/definitions/${category}`);
            if (!response.ok) throw new Error("Failed to fetch data");
            const data = await response.json();
            setItems(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleAdd = async (e) => {
        e.preventDefault();
        if (!newItem.trim()) return;

        try {
            const response = await fetch("http://localhost:8000/api/master/definitions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    category: category,
                    label: newItem,
                    value: newItem // For now, label = value
                })
            });

            if (!response.ok) throw new Error("Failed to add item");
            setNewItem("");
            fetchItems(); // Refresh
        } catch (err) {
            setError(err.message);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure? This will hide the item from dropdowns.")) return;
        try {
            const response = await fetch(`http://localhost:8000/api/master/definitions/${id}`, {
                method: "DELETE"
            });
            if (!response.ok) throw new Error("Failed to delete");
            fetchItems();
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="w-full max-w-4xl mx-auto p-6 animate-fade-in">
            {/* Header */}
            <div className="mb-8 flex items-center space-x-3">
                <div className="p-3 bg-blue-500/20 rounded-xl border border-blue-500/30">
                    <Database className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-white tracking-tight">Master Data Configuration</h1>
                    <p className="text-slate-400">Manage system dropdowns and categories</p>
                </div>
            </div>

            {/* Main Panel */}
            <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl border border-slate-700/50 overflow-hidden shadow-2xl">

                {/* Tabs */}
                <div className="flex border-b border-slate-700/50">
                    <button
                        onClick={() => setCategory("WARD")}
                        className={`flex-1 py-4 text-sm font-semibold tracking-wider transition-all ${category === "WARD"
                                ? "bg-blue-500/10 text-blue-400 border-b-2 border-blue-500"
                                : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                            }`}
                    >
                        HOSPITAL WARDS
                    </button>
                    <button
                        onClick={() => setCategory("SAMPLE_TYPE")}
                        className={`flex-1 py-4 text-sm font-semibold tracking-wider transition-all ${category === "SAMPLE_TYPE"
                                ? "bg-purple-500/10 text-purple-400 border-b-2 border-purple-500"
                                : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                            }`}
                    >
                        SAMPLE TYPES
                    </button>
                </div>

                <div className="p-8">
                    {/* Input Area */}
                    <form onSubmit={handleAdd} className="flex gap-4 mb-8">
                        <input
                            type="text"
                            value={newItem}
                            onChange={(e) => setNewItem(e.target.value)}
                            placeholder={`Add new ${category === 'WARD' ? 'Ward' : 'Sample Type'}...`}
                            className="flex-1 bg-slate-800/50 border border-slate-600/50 rounded-xl px-5 py-3 text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all placeholder-slate-500"
                        />
                        <button
                            type="submit"
                            className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-blue-500/20 flex items-center space-x-2 transition-transform active:scale-95"
                        >
                            <Plus className="w-5 h-5" />
                            <span>Add</span>
                        </button>
                    </form>

                    {/* List Area */}
                    {loading ? (
                        <div className="text-center py-10 text-slate-500 animate-pulse">Loading data...</div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {items.map((item) => (
                                <div key={item.id} className="group bg-slate-800/30 border border-slate-700/50 rounded-xl p-4 flex justify-between items-center hover:bg-slate-800 transition-all">
                                    <span className="font-medium text-slate-200">{item.label}</span>
                                    <button
                                        onClick={() => handleDelete(item.id)}
                                        className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                        title="Delete"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}

                    {!loading && items.length === 0 && (
                        <div className="text-center py-12 border-2 border-dashed border-slate-700/50 rounded-xl">
                            <p className="text-slate-500">No items found. Add one above.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MasterDataManager;
