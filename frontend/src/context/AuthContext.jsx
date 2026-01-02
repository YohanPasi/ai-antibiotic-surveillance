import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('token'));
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Auto-login if token exists
        if (token) {
            // In a real app, verify token validity with /api/users/me
            // For now, we decode basic details or just trust it until 401
            fetchProfile(token);
        } else {
            setLoading(false);
        }
    }, [token]);

    const fetchProfile = async (authToken) => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/api/users/me`, {
                headers: { 'Authorization': `Bearer ${authToken}` }
            });
            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
            } else {
                logout(); // Invalid token
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const login = async (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${import.meta.env.VITE_API_URL}/api/auth/token`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();
        const accessToken = data.access_token;

        localStorage.setItem('token', accessToken);
        setToken(accessToken);
        // User state will be updated by useEffect -> fetchProfile
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
    };

    const value = {
        user,
        token,
        loading,
        login,
        logout,
        isAuthenticated: !!user
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
    return useContext(AuthContext);
};
