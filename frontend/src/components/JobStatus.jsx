import { useState } from 'react'
import client from '../api/client'

export default function JobStatus({ jobId }) {
  const [jobData, setJobData] = useState(null)
  const [status, setStatus] = useState('')

  const fetchJob = async () => {
    if (!jobId) return setStatus('No jobId')
    setStatus('Fetching job status...')
    try {
      const res = await client.get(`/jobs/${jobId}`)
      setJobData(res.data)
      setStatus('Job status fetched.')
    } catch (err) {
      console.error(err)
      setStatus(`Error: ${err.message}`)
    }
  }

  return (
    <div>
      <h2>Job Status</h2>
      <div style={{ marginBottom: '0.5rem' }}>
        <button onClick={fetchJob} disabled={!jobId}>
          Refresh Job Status
        </button>
      </div>
      <pre style={{ marginTop: '0.5rem', whiteSpace: 'pre-wrap' }}>
        {jobData ? JSON.stringify(jobData, null, 2) : 'No job loaded yet.'}
      </pre>
      <div style={{ marginTop: '0.5rem' }}>
        <strong>Status:</strong> {status || 'Idle'}
      </div>
    </div>
  )
}
