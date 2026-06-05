// Certificates.jsx — list comes from GET /api/certificates; "Generate" calls
// POST /api/certificates/generate, which the BACKEND validates (it refuses if
// the course isn't "Completed"). So the success/failure message is real.
import { useState, useEffect } from "react";
import CertificateList from "../components/CertificateList.jsx";
import { getCertificates, generateCertificate } from "../services/api.js";

export default function Certificates() {
  const [rows, setRows] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getCertificates().then(setRows).catch((e) => setError(e.message));
  }, []);

  const handleGenerate = async (cert) => {
    setMessage(""); setError("");
    try {
      const res = await generateCertificate(cert.student, cert.course);
      setMessage(`${res.message} ✓`);
    } catch (e) {
      setError(e.message); // e.g. "Cannot generate — course not completed."
    }
  };

  return (
    <>
      {message && (
        <div className="panel" style={{ marginBottom: "1rem" }}>
          <span className="badge badge-success">{message}</span>
        </div>
      )}
      {error && <p className="form-error">{error}</p>}
      <CertificateList rows={rows} onGenerate={handleGenerate} />
    </>
  );
}
