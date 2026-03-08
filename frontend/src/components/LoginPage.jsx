import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { Lock, User } from 'lucide-react';

const LoginPage = () => {
    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Redirect to where user wanted to go, or home
    const from = location.state?.from?.pathname || "/";

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setIsSubmitting(true);
        try {
            await login(username, password);
            navigate(from, { replace: true });
        } catch (err) {
            setError(err.message);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-900 border-t-4 border-purple-600">
            <div className="bg-gray-800 p-8 rounded-lg shadow-2xl w-full max-w-md border border-gray-700">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">System Access</h1>
                    <p className="text-gray-400 text-sm">Surveillance & Prediction Engine</p>
                </div>

                {error && (
                    <div className="bg-red-900/50 border border-red-700 text-red-200 p-3 rounded mb-6 text-sm flex items-center justify-center">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="relative">
                        <User className="absolute left-3 top-3 text-gray-500 w-5 h-5" />
                        <input
                            type="text"
                            placeholder="Username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full bg-gray-900 text-white pl-10 pr-4 py-3 rounded border border-gray-700 focus:border-purple-500 focus:outline-none transition-colors"
                        />
                    </div>
                    <div className="relative">
                        <Lock className="absolute left-3 top-3 text-gray-500 w-5 h-5" />
                        <input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full bg-gray-900 text-white pl-10 pr-4 py-3 rounded border border-gray-700 focus:border-purple-500 focus:outline-none transition-colors"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-3 rounded transition-all shadow-lg text-sm uppercase tracking-wider disabled:opacity-50"
                    >
                        {isSubmitting ? 'Authenticating...' : 'Enter Secure Area'}
                    </button>
                </form>

                <div className="mt-6 text-center text-xs text-gray-500">
                    Restricted Access. Authorized Personnel Only.
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
