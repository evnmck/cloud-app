
import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import styles from './Login.module.css'

export default function Login() {
  const [tokenInput, setTokenInput] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const location = useLocation()
  const { token, login } = useAuth()

  const from = location.state?.from?.pathname || '/'

  // If already logged in, redirect to dashboard
  useEffect(() => {
    if (token) navigate(from, { replace: true })
  }, [token, from, navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!tokenInput) return setError('Please enter an API token')
    try {
      localStorage.setItem('api_token', tokenInput)
      login(tokenInput)
      // navigate will be triggered by useEffect when token updates
    } catch (err) {
      setError('Login failed')
    }
  }

  // Only show form if not logged in
  if (token) return null

  return (
    <div className={styles.container}>
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <div className={styles.formGroup}>
          <label>API Token</label>
          <input
            className={styles.fullWidth}
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
          />
        </div>
        {error && <div className={styles.error}>{error}</div>}
        <div className={styles.buttonRow}>
          <button type="submit">Login</button>
        </div>
      </form>
    </div>
  )
}

