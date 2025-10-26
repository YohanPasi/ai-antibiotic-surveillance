import { useState } from "react";
import MrsaDashboard from "./pages/MrsaDashboard";

function App() {
  const [currentPage, setCurrentPage] = useState("mrsa");

  return (
    <div style={{ fontFamily: "system-ui, Arial, sans-serif", width: "100%", margin: 0, padding: 0 }}>
      {currentPage === "mrsa" && <MrsaDashboard />}
    </div>
  );
}

export default App;
