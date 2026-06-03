// Certificates.jsx — owns certificate state; "Generate" shows feedback.
import { useState } from "react";
import CertificateList from "../components/CertificateList.jsx";
import { certificates } from "../services/mockData.js";

export default function Certificates() {
  const [rows] = useState(certificates);
  const [message, setMessage] = useState("");

  const handleGenerate = (cert) => {
    setMessage(`Certificate generated for ${cert.student} — ${cert.course} ✓`);
  };

  return (
    <>
      {message && (
        <div className="panel" style={{ marginBottom: "1rem" }}>
          <span className="badge badge-success">{message}</span>
        </div>
      )}
      <CertificateList rows={rows} onGenerate={handleGenerate} />
    </>
  );
}
