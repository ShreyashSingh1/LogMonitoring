// Socket.IO configuration
export const SOCKET_URL = import.meta.env.PROD
  ? window.location.origin // Production: use same origin
  : "http://127.0.0.1:5000"; // Development: connect directly to backend

export const SOCKET_OPTIONS = {
  transports: ["websocket", "polling"],
  upgrade: true,
  rememberUpgrade: true,
  reconnection: true,
  reconnectionAttempts: 50, 
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  timeout: 20000,
  autoConnect: true,
  forceNew: true,
  withCredentials: false, // Change to false for development
  path: "/socket.io/",
};
