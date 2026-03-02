import { useState, useEffect } from 'react'
import client from '../api/client'

export default function UploadForm({ onUploaded }) {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('')
  const [jobId, setJobId] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)
  const [isPolling, setIsPolling] = useState(false)

  const handleFileChange = (e) => {
    setFile(e.target.files?.[0] || null)
    setStatus('')
  }

  const handleUpload = async () => {
    if (!file) return setStatus('Please choose a file first.')
    setStatus('Requesting upload URL...')
    try {
      const contentType = file.type || 'application/octet-stream'
      const res = await client.post('/uploads', { filename: file.name, contentType })
      const { uploadUrl, jobId: jId, uploadKey, bucket } = res.data
      
      setJobId(jId)
      setStatus('Uploading to S3...')

      const putRes = await fetch(uploadUrl, {
        method: 'PUT',
        headers: { 'Content-Type': contentType },
        body: file,
      })

      if (!putRes.ok) {
        const errText = await putRes.text()
        throw new Error(`S3 upload failed: ${putRes.status} ${errText}`)
      }

      setStatus(`Upload complete. Processing pipeline started...`)
      setJobStatus('UPLOADED')
      setIsPolling(true)
      onUploaded?.({ jobId: jId, uploadKey, bucket })
    } catch (err) {
      console.error(err)
      setStatus(`Error: ${err.message}`)
      setIsPolling(false)
    }
  }

  // Poll job status while processing
  useEffect(() => {
    if (!isPolling || !jobId) return

    const interval = setInterval(async () => {
      try {
        const res = await client.get(`/jobs/${jobId}`)
        const newStatus = res.data.status
        setJobStatus(newStatus)

        if (newStatus === 'PROCESSED' || newStatus === 'COMPLETED') {
          setStatus(`✓ Pipeline complete! Status: ${newStatus}`)
          setIsPolling(false)
        } else if (newStatus === 'FAILED') {
          setStatus(`✗ Pipeline failed: ${res.data.error || 'Unknown error'}`)
          setIsPolling(false)
        } else {
          setStatus(`Processing: ${newStatus}`)
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }, 2000) // Poll every 2 seconds

    return () => clearInterval(interval)
  }, [isPolling, jobId])

  return (
    <div>
      <h2>Upload a file</h2>
      <input type="file" onChange={handleFileChange} disabled={isPolling} />
      <div style={{ marginTop: '0.5rem' }}>
        <button onClick={handleUpload} disabled={!file || isPolling}>
          Start Upload
        </button>
      </div>
      <div style={{ marginTop: '0.5rem' }}>
        <strong>Status:</strong> {status || 'Idle'}
        {jobId && <div style={{ marginTop: '0.25rem', fontSize: '0.9rem', color: '#666' }}>Job ID: {jobId}</div>}
      </div>
    </div>
  )
}
