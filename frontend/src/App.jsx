import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AuthProvider from "./auth/AuthProvider";
import ProtectedRoute from "./auth/ProtectedRoute";

import Login from "./pages/Login";
import Register from "./pages/Register";
import ModuleSelect from "./pages/ModuleSelect";
import MrsaDashboard from "./mrsa/MrsaDashboard";
import EsblDashboard from "./esbl/EsblDashboard";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route path="/modules" element={
            <ProtectedRoute>
              <ModuleSelect />
            </ProtectedRoute>
          } />

          <Route path="/mrsa" element={
            <ProtectedRoute>
              <MrsaDashboard />
            </ProtectedRoute>
          } />

          <Route path="/esbl" element={
            <ProtectedRoute>
              <EsblDashboard />
            </ProtectedRoute>
          } />

          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
