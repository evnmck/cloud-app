import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import client from '../api/client'
import UploadForm from '../components/UploadForm'
import JobStatus from '../components/JobStatus'
import styles from './Dashboard.module.css'

export default function Dashboard() {
  const { token, logout } = useAuth()
  const [health, setHealth] = useState(null)
  const [lastJobId, setLastJobId] = useState('')

  const checkHealth = async () => {
    if (!token) return setHealth({ error: 'Not authenticated' })
    try {
      const res = await client.get('/health')
      setHealth(res.data)
    } catch (err) {
      setHealth({ error: 'Failed to call /health', details: err.message })
    }
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>MyApp</h1>
        <div>
          <button onClick={logout}>Logout</button>
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
        <UploadForm onUploaded={(info) => setLastJobId(info.jobId)} />
      </section>

      <section>
        <JobStatus jobId={lastJobId} />
      </section>
    </div>
  )
}
