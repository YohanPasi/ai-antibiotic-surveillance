import { useEffect, useState } from "react";
import { getPatients, createPatient } from "./api/api";

function App() {
  const [patients, setPatients] = useState([]);

  useEffect(() => {
    async function fetchPatients() {
      const data = await getPatients();
      setPatients(data);
    }
    fetchPatients();
  }, []);

  const handleAdd = async () => {
    const newPatient = {
      age: 42,
      sex: "Male",
      ward: "ICU",
      diagnosis: "Sepsis",
    };
    await createPatient(newPatient);
    const data = await getPatients();
    setPatients(data);
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>AI Antibiotic Surveillance</h1>
      <button onClick={handleAdd}>Add Sample Patient</button>
      <ul>
        {patients.map((p) => (
          <li key={p.patient_id}>
            {p.age} yrs | {p.sex} | {p.ward} | {p.diagnosis}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
