import { BrowserRouter, Routes, Route } from "react-router-dom";
import ModuleSelect from "../pages/ModuleSelect";
import MrsaDashboard from "../mrsa/MrsaDashboard";
import EsblDashboard from "../esbl/EsblDashboard";

export default function Router() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ModuleSelect />} />
        <Route path="/mrsa" element={<MrsaDashboard />} />
        <Route path="/esbl" element={<EsblDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
