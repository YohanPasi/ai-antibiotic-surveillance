import { useNavigate } from "react-router-dom";

export default function ModuleSelect() {
  const navigate = useNavigate();

  return (
    <div style={{ padding: 40 }}>
      <h1>Select Analysis Module</h1>

      <button onClick={() => navigate("/mrsa")} style={{ marginRight: 10 }}>
        MRSA Dashboard
      </button>

      <button onClick={() => navigate("/esbl")}>
        ESBL Dashboard
      </button>
    </div>
  );
}
