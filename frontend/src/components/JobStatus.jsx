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

  const getStatusColor = (status) => {
    switch (status) {
      case 'COMPLETED': return '#4caf50'
      case 'FAILED': return '#f44336'
      case 'PROCESSING': return '#2196f3'
      default: return '#666'
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
      
      {jobData && (
        <div style={{ marginTop: '1rem', padding: '1rem', border: '1px solid #ddd' }}>
          <div><strong>Job ID:</strong> {jobData.jobId}</div>
          <div><strong>Status:</strong> <span style={{ color: getStatusColor(jobData.status) }}>{jobData.status}</span></div>
          <div><strong>Filename:</strong> {jobData.filename}</div>
          <div><strong>Created:</strong> {new Date(jobData.createdAt).toLocaleString()}</div>
          <div><strong>Updated:</strong> {new Date(jobData.updatedAt).toLocaleString()}</div>
          
          {jobData.processedDataLocation && (
            <div><strong>Processed Data:</strong> <a href={jobData.processedDataLocation} target="_blank" rel="noopener noreferrer">{jobData.processedDataLocation}</a></div>
          )}
          
          {jobData.error && (
            <div style={{ color: '#f44336' }}><strong>Error:</strong> {jobData.error}</div>
          )}
        </div>
      )}
      
      <pre style={{ marginTop: '0.5rem', whiteSpace: 'pre-wrap', fontSize: '0.85rem' }}>
        {jobData ? JSON.stringify(jobData, null, 2) : 'No job loaded yet.'}
      </pre>
      <div style={{ marginTop: '0.5rem' }}>
        <strong>Status:</strong> {status || 'Idle'}
      </div>
    </div>
  )
}
