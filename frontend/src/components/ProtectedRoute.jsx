import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children }) => {
    const { user, loading } = useAuth();
    const location = useLocation();

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center gap-4">
                <div className="text-purple-400 animate-pulse">Security Check...</div>
                <button
                    onClick={() => {
                        localStorage.removeItem('token');
                        window.location.reload();
                    }}
                    className="text-xs text-gray-500 hover:text-gray-300 underline"
                >
                    Stuck? Click to Reset
                </button>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return children;
};

export default ProtectedRoute;
