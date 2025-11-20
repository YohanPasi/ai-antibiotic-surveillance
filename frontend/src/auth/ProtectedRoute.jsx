import { Navigate } from "react-router-dom";
import { useAuth } from "./useAuth";
import { useEffect } from "react";

export default function ProtectedRoute({ children }) {
  const { user, loading, token } = useAuth();

  // Double-check token exists in localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken && !loading) {
      // Token was cleared, but state hasn't updated yet
      // This will trigger a re-render when AuthProvider detects the change
    }
  }, [loading, token]);

  if (loading) {
    return (
      <div style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        fontSize: "1.2rem",
        color: "#4a5568"
      }}>
        Checking authentication...
      </div>
    );
  }

  if (!user || !token) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
