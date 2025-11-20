import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AuthProvider from "./auth/AuthProvider";
import ProtectedRoute from "./auth/ProtectedRoute";

import Login from "./pages/Login";
import Register from "./pages/Register";
import ModuleSelect from "./pages/ModuleSelect";
import MrsaDashboard from "./mrsa/MrsaDashboard";
import EsblDashboard from "./esbl/EsblDashboard";
import NonfermenterDashboard from "./non_fem/NonfermenterDashboard";
import MainLayout from "./components/layout/MainLayout";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/modules" element={<ModuleSelect />} />
            <Route path="/mrsa" element={<MrsaDashboard />} />
            <Route path="/esbl" element={<EsblDashboard />} />
            <Route path="/nonfermenter" element={<NonfermenterDashboard />} />
            <Route path="/" element={<Navigate to="/modules" replace />} />
            <Route path="*" element={<Navigate to="/modules" replace />} />
          </Route>

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
