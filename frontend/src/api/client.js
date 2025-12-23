import axios from 'axios'
import { getAuthToken } from '../contexts/AuthHelpers' // or import useAuth inside hooks
const client = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL })
client.interceptors.request.use(cfg => {
  const token = localStorage.getItem('api_token')
  if (token) cfg.headers['X-API-TOKEN'] = token
  return cfg
})
export default client