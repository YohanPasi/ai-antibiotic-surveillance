export default function Footer() {
  return (
    <footer className="footer">
      <span>
        <strong>AI-Driven Antibiotic Surveillance</strong> · Teaching Hospital
        Peradeniya × SLIIT
      </span>
      <span>Last sync: {new Date().toLocaleTimeString([], { timeStyle: "short" })}</span>
      <span>© {new Date().getFullYear()} Infection Control Innovation Lab</span>
    </footer>
  );
}

