import { Navigate } from "react-router-dom";
import { useAuth } from "./useAuth";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) return <div>Checking authentication...</div>;

  if (!user) return <Navigate to="/login" />;

  return children;
}
