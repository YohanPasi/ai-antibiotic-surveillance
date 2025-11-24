import { BrowserRouter, Routes, Route } from "react-router-dom";
import ModuleSelect from "../pages/ModuleSelect";
import MrsaDashboard from "../mrsa/MrsaDashboard";
import EsblDashboard from "../esbl/EsblDashboard";
import MrsaModalDashboard from "../pages/MrsaModalDashboard";

export default function Router() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ModuleSelect />} />
        <Route path="/mrsa" element={<MrsaDashboard />} />
        <Route path="/mrsa/prediction" element={<MrsaModalDashboard />} />
        <Route path="/esbl" element={<EsblDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
