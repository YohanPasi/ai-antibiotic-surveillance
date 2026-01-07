import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { Lock, User, Shield, Activity, Database, Brain, AlertCircle, CheckCircle2 } from 'lucide-react';

const LoginPage = () => {
    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

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

    const modules = [
        { name: 'MRSA', icon: Shield, color: 'from-rose-500 to-pink-500', bg: 'bg-rose-50', border: 'border-rose-200', text: 'text-rose-600' },
        { name: 'ESBL', icon: Database, color: 'from-blue-500 to-cyan-500', bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-600' },
        { name: 'Non-Fermenters', icon: Activity, color: 'from-amber-500 to-orange-500', bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-600' },
        { name: 'STP', icon: Brain, color: 'from-purple-500 to-violet-500', bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-600' }
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-emerald-900 to-teal-900 flex items-center justify-center p-6 relative overflow-hidden">
            {/* Animated Background Pattern */}
            <div className="absolute inset-0 opacity-10">
                <div className="absolute top-0 left-0 w-full h-full" style={{
                    backgroundImage: `radial-gradient(circle at 20% 30%, rgba(16, 185, 129, 0.3) 0%, transparent 50%), 
                                     radial-gradient(circle at 80% 70%, rgba(20, 184, 166, 0.3) 0%, transparent 50%)`
                }}></div>
            </div>

            {/* Main Container */}
            <div className="relative z-10 w-full max-w-6xl">
                <div className="grid lg:grid-cols-5 gap-8 items-center">

                    {/* Left Section - Branding (3 columns) */}
                    <div className="lg:col-span-3 text-white">
                        {/* Logo */}
                        <div className="flex items-center gap-4 mb-8">
                            <div className="relative">
                                <div className="absolute inset-0 bg-gradient-to-br from-emerald-400 to-teal-400 rounded-2xl blur-xl opacity-50 animate-pulse"></div>
                                <div className="relative w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-2xl flex items-center justify-center shadow-2xl border border-white/20">
                                    <span className="text-3xl font-bold">S</span>
                                </div>
                            </div>
                            <div>
                                <h1 className="text-4xl font-bold tracking-tight">Sentinel</h1>
                                <p className="text-emerald-300 font-medium text-sm">Antimicrobial Resistance Surveillance</p>
                            </div>
                        </div>

                        {/* Headline */}
                        <div className="mb-12">
                            <h2 className="text-5xl font-bold leading-tight mb-4 bg-gradient-to-r from-white via-emerald-100 to-teal-100 bg-clip-text text-transparent">
                                Intelligent Pathogen Detection
                            </h2>
                            <p className="text-xl text-emerald-100 leading-relaxed max-w-xl">
                                AI-powered real-time surveillance system for predicting antibiotic resistance and detecting hospital outbreaks.
                            </p>
                        </div>

                        {/* Module Grid */}
                        <div className="grid grid-cols-2 gap-4 mb-8">
                            {modules.map((module, idx) => {
                                const Icon = module.icon;
                                return (
                                    <div key={idx} className="group relative">
                                        <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-white/5 rounded-2xl blur group-hover:blur-md transition-all"></div>
                                        <div className="relative bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-5 hover:bg-white/15 transition-all duration-300 cursor-pointer hover:scale-105 hover:border-white/40">
                                            <div className={`w-12 h-12 bg-gradient-to-br ${module.color} rounded-xl flex items-center justify-center mb-3 shadow-lg`}>
                                                <Icon className="w-6 h-6 text-white" />
                                            </div>
                                            <h3 className="font-bold text-lg mb-1">{module.name}</h3>
                                            <div className="flex items-center gap-1.5 text-xs text-emerald-200">
                                                <CheckCircle2 className="w-3.5 h-3.5" />
                                                <span>Active</span>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Stats */}
                        <div className="flex items-center gap-8 p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl">
                            <div className="flex-1 text-center">
                                <p className="text-3xl font-bold text-emerald-400">4+</p>
                                <p className="text-xs text-emerald-100 mt-1">Pathogen Modules</p>
                            </div>
                            <div className="w-px h-12 bg-white/20"></div>
                            <div className="flex-1 text-center">
                                <p className="text-3xl font-bold text-emerald-400">AI</p>
                                <p className="text-xs text-emerald-100 mt-1">Powered Analytics</p>
                            </div>
                            <div className="w-px h-12 bg-white/20"></div>
                            <div className="flex-1 text-center">
                                <p className="text-3xl font-bold text-emerald-400">24/7</p>
                                <p className="text-xs text-emerald-100 mt-1">Real-time Monitor</p>
                            </div>
                        </div>
                    </div>

                    {/* Right Section - Login Form (2 columns) */}
                    <div className="lg:col-span-2">
                        {/* Mobile Logo */}
                        <div className="lg:hidden mb-8 text-center">
                            <div className="inline-flex items-center gap-3 mb-6">
                                <div className="w-14 h-14 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl flex items-center justify-center shadow-xl">
                                    <span className="text-2xl font-bold text-white">S</span>
                                </div>
                                <div className="text-left text-white">
                                    <h1 className="text-2xl font-bold">Sentinel</h1>
                                    <p className="text-emerald-300 text-sm">AMR Surveillance</p>
                                </div>
                            </div>
                        </div>

                        {/* Login Card */}
                        <div className="bg-white rounded-3xl shadow-2xl p-8 border border-slate-200">
                            <div className="mb-6">
                                <h3 className="text-2xl font-bold text-slate-900 mb-1">Welcome Back</h3>
                                <p className="text-slate-600 text-sm">Enter credentials to access the platform</p>
                            </div>

                            {/* Error Alert */}
                            {error && (
                                <div className="mb-5 bg-red-50 border-l-4 border-red-500 rounded-r-xl p-4 flex items-start gap-3 animate-fadeIn">
                                    <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                                    <div>
                                        <p className="text-red-800 font-semibold text-sm">Authentication Failed</p>
                                        <p className="text-red-600 text-xs mt-0.5">{error}</p>
                                    </div>
                                </div>
                            )}

                            {/* Form */}
                            <form onSubmit={handleSubmit} className="space-y-5">
                                {/* Username */}
                                <div>
                                    <label htmlFor="username" className="block text-sm font-semibold text-slate-700 mb-2">
                                        Username
                                    </label>
                                    <div className="relative">
                                        <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                        <input
                                            id="username"
                                            type="text"
                                            value={username}
                                            onChange={(e) => setUsername(e.target.value)}
                                            className="w-full pl-11 pr-4 py-3 bg-slate-50 border-2 border-slate-200 rounded-xl
                                            focus:border-emerald-500 focus:bg-white focus:ring-4 focus:ring-emerald-500/10 
                                            outline-none transition-all text-slate-900 placeholder:text-slate-400"
                                            placeholder="Enter username"
                                            required
                                            autoComplete="username"
                                        />
                                    </div>
                                </div>

                                {/* Password */}
                                <div>
                                    <label htmlFor="password" className="block text-sm font-semibold text-slate-700 mb-2">
                                        Password
                                    </label>
                                    <div className="relative">
                                        <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                        <input
                                            id="password"
                                            type="password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            className="w-full pl-11 pr-4 py-3 bg-slate-50 border-2 border-slate-200 rounded-xl
                                            focus:border-emerald-500 focus:bg-white focus:ring-4 focus:ring-emerald-500/10 
                                            outline-none transition-all text-slate-900 placeholder:text-slate-400"
                                            placeholder="Enter password"
                                            required
                                            autoComplete="current-password"
                                        />
                                    </div>
                                </div>

                                {/* Submit Button */}
                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="w-full mt-2 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold py-3.5 rounded-xl
                                    hover:from-emerald-700 hover:to-teal-700 focus:ring-4 focus:ring-emerald-500/50 
                                    disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-emerald-600/30
                                    hover:shadow-xl hover:shadow-emerald-600/50 transform hover:-translate-y-0.5 active:translate-y-0"
                                >
                                    {isSubmitting ? (
                                        <span className="flex items-center justify-center gap-2">
                                            <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                            </svg>
                                            Authenticating...
                                        </span>
                                    ) : (
                                        'Sign In to Dashboard'
                                    )}
                                </button>
                            </form>

                            {/* Footer */}
                            <div className="mt-6 pt-5 border-t border-slate-200 text-center">
                                <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
                                    <Lock className="w-3.5 h-3.5" />
                                    <span>Encrypted · Authorized access only</span>
                                </div>
                            </div>
                        </div>

                        {/* Bottom Text */}
                        <p className="text-center mt-4 text-xs text-emerald-200">
                            Enterprise antimicrobial resistance platform
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
