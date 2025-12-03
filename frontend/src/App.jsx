import { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const API_TOKEN = import.meta.env.VITE_API_TOKEN;

function App() {
  const [health, setHealth] = useState(null);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [jobId, setJobId] = useState("");
  const [jobData, setJobData] = useState(null);

  const checkHealth = async () => {
    console.log("API_BASE_URL:", API_BASE_URL);
    console.log("API_TOKEN present:", !!API_TOKEN);

    try {
      const res = await fetch(`${API_BASE_URL}/health`, {
        headers: {
          "X-API-TOKEN": API_TOKEN,
        },
      });
      console.log("Health response status:", res.status);
      const data = await res.json();
      setHealth(data);
    } catch (err) {
      console.error("Health call failed:", err);
      setHealth({
        error: "Failed to call /health",
        details: String(err),
      });
    }
  };

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0] || null;
    setFile(selected);
    setStatus("");
    setJobId("");
    setJobData(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setStatus("Please choose a file first.");
      return;
    }

    setStatus("Requesting upload URL...");
    try {
      const contentType = file.type || "application/octet-stream";

      // 1) Call POST /uploads to get jobId + presigned URL
      const res = await fetch(`${API_BASE_URL}/uploads`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-TOKEN": API_TOKEN,
        },
        body: JSON.stringify({
          filename: file.name,
          contentType,
        }),
      });

      if (!res.ok) {
        const errBody = await res.text();
        throw new Error(`POST /uploads failed: ${res.status} ${errBody}`);
      }

      const { uploadUrl, jobId, uploadKey, bucket } = await res.json();
      setJobId(jobId);
      setStatus(`Got upload URL. Uploading to S3...`);

      // 2) Upload the file directly to S3 using the presigned URL
      const putRes = await fetch(uploadUrl, {
        method: "PUT",
        headers: {
          "Content-Type": contentType,
        },
        body: file,
      });

      if (!putRes.ok) {
        const errText = await putRes.text();
        throw new Error(`S3 upload failed: ${putRes.status} ${errText}`);
      }

      setStatus(
        `Upload complete. Job ID: ${jobId}. S3 key: ${uploadKey} in bucket ${bucket}`
      );
    } catch (err) {
      console.error(err);
      setStatus(`Error: ${err.message}`);
    }
  };

  const fetchJobStatus = async () => {
    if (!jobId) {
      setStatus("No jobId yet – upload a file first.");
      return;
    }
    setStatus("Fetching job status...");
    try {
      const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
        headers: {
          "X-API-TOKEN": API_TOKEN,
        },
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.message || "Failed to fetch job");
      }
      setJobData(data);
      setStatus("Job status fetched.");
    } catch (err) {
      console.error(err);
      setStatus(`Error: ${err.message}`);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "2rem auto", fontFamily: "system-ui" }}>
      <h1>MyApp – Upload Tester</h1>

      <section style={{ marginBottom: "1.5rem" }}>
        <button onClick={checkHealth}>Check API Health</button>
        <div style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>
          <strong>Health:</strong>{" "}
          <pre style={{ whiteSpace: "pre-wrap" }}>
            {health ? JSON.stringify(health, null, 2) : "Not checked yet"}
          </pre>
        </div>
      </section>

      <section style={{ marginBottom: "1.5rem" }}>
        <h2>Upload a file</h2>
        <input type="file" onChange={handleFileChange} />
        <div style={{ marginTop: "0.5rem" }}>
          <button onClick={handleUpload} disabled={!file}>
            Start Upload
          </button>
        </div>
      </section>

      <section style={{ marginBottom: "1.5rem" }}>
        <div>
          <strong>Status:</strong> {status || "Idle"}
        </div>
        {jobId && (
          <div style={{ marginTop: "0.5rem" }}>
            <strong>Job ID:</strong> {jobId}
          </div>
        )}
      </section>

      <section>
        <h2>Job Status</h2>
        <button onClick={fetchJobStatus} disabled={!jobId}>
          Refresh Job Status
        </button>
        <pre style={{ marginTop: "0.5rem", whiteSpace: "pre-wrap" }}>
          {jobData ? JSON.stringify(jobData, null, 2) : "No job loaded yet."}
        </pre>
      </section>
    </div>
  );
}

export default App;
