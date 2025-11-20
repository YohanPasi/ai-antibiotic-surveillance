import { createContext, useState, useEffect, useCallback } from "react";
import { verifyToken } from "../api/api_auth";

export const AuthContext = createContext();

export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  // Function to check and update auth state
  const checkAuth = useCallback(async () => {
    const storedToken = localStorage.getItem("token");
    
    // If token was removed from localStorage, clear state immediately
    if (!storedToken) {
      setUser(null);
      setToken(null);
      setLoading(false);
      return;
    }

    // If token exists but state doesn't match, update state
    if (storedToken !== token) {
      setToken(storedToken);
    }

    // Verify token if it exists
    if (storedToken) {
      try {
        const data = await verifyToken(storedToken);
        if (data?.valid) {
          setUser(data.user);
        } else {
          setUser(null);
          setToken(null);
          localStorage.removeItem("token");
        }
      } catch (error) {
        console.error("Token verification failed:", error);
        setUser(null);
        setToken(null);
        localStorage.removeItem("token");
      } finally {
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, [token]);

  // Initial check on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Listen for storage changes (when localStorage is cleared externally)
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === "token" || e.key === null) {
        // Token was removed or all storage was cleared
        checkAuth();
      }
    };

    // Handle focus event (when user comes back to tab after clearing cookies)
    const handleFocus = () => {
      const storedToken = localStorage.getItem("token");
      if (!storedToken && token) {
        // Token was removed while tab was inactive
        checkAuth();
      }
    };

    // Listen for storage events (works across tabs)
    window.addEventListener("storage", handleStorageChange);
    // Listen for focus events (when user returns to tab)
    window.addEventListener("focus", handleFocus);

    // Also poll localStorage periodically to catch manual clears
    const interval = setInterval(() => {
      const storedToken = localStorage.getItem("token");
      if (!storedToken && token) {
        // Token was removed
        checkAuth();
      } else if (storedToken && !token) {
        // Token was added
        checkAuth();
      }
    }, 500); // Check every 500ms for faster response

    return () => {
      window.removeEventListener("storage", handleStorageChange);
      window.removeEventListener("focus", handleFocus);
      clearInterval(interval);
    };
  }, [token, checkAuth]);

  function login(userData, accessToken) {
    setUser(userData);
    setToken(accessToken);
    localStorage.setItem("token", accessToken);
  }

  function logout() {
    setUser(null);
    setToken(null);
    localStorage.removeItem("token");
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}
