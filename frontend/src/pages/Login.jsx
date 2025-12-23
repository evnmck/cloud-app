import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import client from '../api/client'

export default function Login() {
  const [tokenInput, setTokenInput] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { login } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    // If you have an API login endpoint, call it here. For now accept token directly.
    if (!tokenInput) return setError('Please enter an API token')
    // Optionally validate token by calling /health
    try {
      localStorage.setItem('api_token', tokenInput)
      login(tokenInput)
      navigate('/')
    } catch (err) {
      setError('Login failed')
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '0.5rem' }}>
          <label>API Token</label>
          <input value={tokenInput} onChange={(e) => setTokenInput(e.target.value)} style={{ width: '100%' }} />
        </div>
        {error && <div style={{ color: 'red' }}>{error}</div>}
        <button type="submit">Login</button>
      </form>
    </div>
  )
}
