import { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";
const stages = [
  ["Files received", "3 / 3", "complete"],
  ["Validation", "2 passed, 1 needs review", "attention"],
  ["Manager approval", "Waiting on validation", "pending"],
];

export default function App() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");

  async function upload(event) {
    event.preventDefault();
    if (!file) return;
    setMessage("Requesting a secure upload URL…");
    try {
      const response = await fetch(`${API_URL}/uploads`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Demo-Role": "analyst" },
        body: JSON.stringify({
          cycle_id: "2026-Q2",
          dataset: "participant-outcomes",
          filename: file.name,
        }),
      });
      if (!response.ok) throw new Error(`API returned ${response.status}`);
      const uploadDetails = await response.json();
      const put = await fetch(uploadDetails.upload_url, {
        method: "PUT",
        headers: { "Content-Type": "text/csv" },
        body: file,
      });
      if (!put.ok) throw new Error(`S3 returned ${put.status}`);
      setMessage("Upload received. Automated validation has started.");
    } catch (error) {
      setMessage(`Upload could not be completed: ${error.message}`);
    }
  }

  return (
    <main>
      <header>
        <div className="mark" aria-hidden="true">PH</div>
        <div><p className="eyebrow">Internal operations</p><h1>Reporting portal</h1></div>
        <span className="environment">Synthetic demo</span>
      </header>

      <section className="hero">
        <div><p className="eyebrow">Active reporting cycle</p><h2>Quarter 2 · 2026</h2><p className="lede">Due July 15 · 25 days remaining</p></div>
        <div className="progress" aria-label="Cycle progress"><strong>67%</strong><span>ready for approval</span></div>
      </section>

      <section className="grid">
        <article className="card upload-card">
          <p className="eyebrow">Submit dataset</p><h3>Participant outcomes</h3>
          <p>CSV only. Files are encrypted and uploaded directly to controlled storage.</p>
          <form onSubmit={upload}>
            <label className="dropzone"><span>{file ? file.name : "Choose a CSV file"}</span><input type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files[0])} /></label>
            <button type="submit" disabled={!file}>Upload securely</button>
          </form>
          {message && <p className="message" role="status">{message}</p>}
        </article>

        <article className="card">
          <p className="eyebrow">Cycle status</p><h3>Workflow checkpoints</h3>
          <ol className="stages">
            {stages.map(([label, detail, state]) => (
              <li key={label} className={state}><span className="dot" aria-hidden="true" /><div><strong>{label}</strong><small>{detail}</small></div></li>
            ))}
          </ol>
        </article>
      </section>

      <section className="notice"><strong>1 file needs attention</strong><span>Service encounters · 4 validation errors</span><button className="text-button" type="button">Review errors →</button></section>
    </main>
  );
}
