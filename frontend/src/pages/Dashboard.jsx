import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useWebSocket } from '../hooks/useWebSocket'
import client from '../api/client'
import UploadForm from '../components/UploadForm'
import JobStatus from '../components/JobStatus'
import styles from './Dashboard.module.css'

export default function Dashboard() {
  const navigate = useNavigate()
  const { token, logout } = useAuth()
  const [health, setHealth] = useState(null)
  const [lastJobId, setLastJobId] = useState('')
  const { isConnected, error, connectionId, lastUpdate } = useWebSocket()
  const [jobStatus, setJobStatus] = useState(null)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const checkHealth = async () => {
    if (!token) return setHealth({ error: 'Not authenticated' })
    try {
      const res = await client.get('/health')
      setHealth(res.data)
    } catch (err) {
      setHealth({ error: 'Failed to call /health', details: err.message })
    }
  }

  // Listen for WebSocket job status updates
  useEffect(() => {
    if (lastUpdate && lastUpdate.jobId) {
      setJobStatus(lastUpdate)
      // Optionally update lastJobId if this is a new job
      if (!lastJobId) {
        setLastJobId(lastUpdate.jobId)
      }
    }
  }, [lastUpdate, lastJobId])

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>MyApp</h1>
        <div>
          <button onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <section className={styles.section}>
        <button onClick={checkHealth}>Check API Health</button>
        <div className={styles.status}>
          <strong>Health:</strong>{' '}
          <pre className={styles.pre}>{health ? JSON.stringify(health, null, 2) : 'Not checked yet'}</pre>
        </div>
      </section>

      <section className={styles.section}>
        <h2>WebSocket Connection</h2>
        <div>
          <p>Status: <strong style={{ color: isConnected ? 'green' : 'red' }}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </strong></p>
          {connectionId && <p>Connection ID: <code>{connectionId}</code></p>}
          {error && <p style={{ color: 'red' }}>Error: {error}</p>}
        </div>
      </section>

      <section className={styles.section}>
        <UploadForm onUploaded={(info) => setLastJobId(info.jobId)} />
      </section>

      <section>
        {/* TODO: When job status reaches 'PROCESSED', automatically fetch full job details 
            via GET /jobs/{jobId} to populate results/processed data location for download */}
        <JobStatus jobId={lastJobId} realtimeUpdate={jobStatus} />
      </section>
    </div>
  )
}
