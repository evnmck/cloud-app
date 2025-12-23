import React, { createContext, useState, useContext } from 'react'
const AuthContext = createContext()
export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('api_token') || null)
  const login = (newToken) => { setToken(newToken); localStorage.setItem('api_token', newToken) }
  const logout = () => { setToken(null); localStorage.removeItem('api_token') }
  return <AuthContext.Provider value={{ token, login, logout }}>{children}</AuthContext.Provider>
}
export const useAuth = () => useContext(AuthContext)