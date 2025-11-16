import { createContext, useState, useEffect } from "react";
import { verifyToken } from "../api/api_auth";

export const AuthContext = createContext();

export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function check() {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const data = await verifyToken(token);
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
    }
    check();
  }, [token]);

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
