import { createContext, useContext, useEffect, useState } from 'react'
import { io } from 'socket.io-client'

const SocketContext = createContext()

export const useSocket = () => {
  const context = useContext(SocketContext)
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider')
  }
  return context
}

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null)
  const [connected, setConnected] = useState(false)
  const [logs, setLogs] = useState([])
  const [errors, setErrors] = useState([])

  useEffect(() => {
    // Connect to Socket.IO server
    const newSocket = io('http://localhost:5000', {
      transports: ['websocket', 'polling']
    })

    newSocket.on('connect', () => {
      console.log('Connected to server')
      setConnected(true)
    })

    newSocket.on('disconnect', () => {
      console.log('Disconnected from server')
      setConnected(false)
    })

    newSocket.on('status', (data) => {
      console.log('Status:', data)
    })

    newSocket.on('new_log', (logEntry) => {
      console.log('New log:', logEntry)
      setLogs(prevLogs => [logEntry, ...prevLogs.slice(0, 999)]) // Keep last 1000 logs
    })

    newSocket.on('error_detected', (errorLog) => {
      console.log('Error detected:', errorLog)
      setErrors(prevErrors => [errorLog, ...prevErrors.slice(0, 99)]) // Keep last 100 errors
    })

    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [])

  const value = {
    socket,
    connected,
    logs,
    errors,
    addLog: (log) => setLogs(prev => [log, ...prev.slice(0, 999)]),
    clearLogs: () => setLogs([]),
    clearErrors: () => setErrors([])
  }

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  )
} 