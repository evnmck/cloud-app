import axios from 'axios'

const client = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL })

client.interceptors.request.use(cfg => {
  const token = localStorage.getItem('api_token')
  if (token) cfg.headers['X-API-TOKEN'] = token
  return cfg
})

export default client