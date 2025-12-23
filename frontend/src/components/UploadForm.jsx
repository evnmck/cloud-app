import { useState } from 'react'
import client from '../api/client'

export default function UploadForm({ onUploaded }) {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('')

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
      const { uploadUrl, jobId, uploadKey, bucket } = res.data
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

      setStatus(`Upload complete. Job ID: ${jobId}`)
      onUploaded?.({ jobId, uploadKey, bucket })
    } catch (err) {
      console.error(err)
      setStatus(`Error: ${err.message}`)
    }
  }

  return (
    <div>
      <h2>Upload a file</h2>
      <input type="file" onChange={handleFileChange} />
      <div style={{ marginTop: '0.5rem' }}>
        <button onClick={handleUpload} disabled={!file}>
          Start Upload
        </button>
      </div>
      <div style={{ marginTop: '0.5rem' }}>
        <strong>Status:</strong> {status || 'Idle'}
      </div>
    </div>
  )
}
