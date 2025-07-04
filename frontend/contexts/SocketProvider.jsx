import { useEffect, useState, useCallback, useMemo } from "react";
import { io } from "socket.io-client";
import { SOCKET_URL, SOCKET_OPTIONS } from "../config/socketConfig";
import { SocketContext } from "./SocketContextDef";
import { createSocketLogService } from "../services/api";

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [logs, setLogs] = useState([]);
  const [errors, setErrors] = useState([]);
  const [connectionAttempts, setConnectionAttempts] = useState(0);

  // Initialize socket connection
  useEffect(() => {
    console.log("🔌 Initializing socket connection");

    const newSocket = io(SOCKET_URL, SOCKET_OPTIONS);

    // Connection event handlers
    newSocket.on("connect", () => {
      console.log("🟢 Socket.IO: Connected to server");
      setConnected(true);
      setConnectionAttempts(0);
    });

    newSocket.on("disconnect", (reason) => {
      console.log("🔴 Socket.IO: Disconnected from server:", reason);
      setConnected(false);
    });

    newSocket.on("connect_error", (error) => {
      console.error("❌ Socket.IO: Connection error:", error);
      console.error("Error details:", {
        message: error.message,
        description: error.description,
        type: error.type,
      });
      setConnected(false);
      setConnectionAttempts((prev) => prev + 1);
    });

    newSocket.on("connect_timeout", () => {
      console.error("❌ Socket.IO: Connection timeout");
      setConnected(false);
    });

    newSocket.on("reconnect", (attemptNumber) => {
      console.log(`🔄 Socket.IO: Reconnected after ${attemptNumber} attempts`);
      setConnected(true);
    });

    newSocket.on("reconnect_error", (error) => {
      console.error("❌ Socket.IO: Reconnection error:", error.message);
    });

    newSocket.on("reconnect_failed", () => {
      console.error("❌ Socket.IO: Failed to reconnect after all attempts");
    });

    // Handle connection_established event
    newSocket.on("connection_established", (data) => {
      console.log("🤝 Socket.IO: Connection established", data);
      if (data.recent_logs) {
        setLogs(data.recent_logs);
      }
    });

    // Handle all log events
    const handleNewLog = (logEntry) => {
      console.log("📝 Socket.IO: Received new log:", logEntry);
      setLogs((prevLogs) => {
        const newLogs = [logEntry, ...prevLogs];
        // Keep last 1000 logs in memory
        return newLogs.slice(0, 1000);
      });

      // If it's an error, also add to errors array
      if (
        logEntry.log_type === "error" ||
        logEntry.level?.toLowerCase() === "error"
      ) {
        setErrors((prevErrors) => {
          const newErrors = [logEntry, ...prevErrors];
          // Keep last 100 errors in memory
          return newErrors.slice(0, 100);
        });
      }
    };

    // Listen to all log events
    newSocket.on("new_log", handleNewLog);
    newSocket.on("new_info_log", handleNewLog);
    newSocket.on("new_error_log", handleNewLog);
    newSocket.on("new_request_log", handleNewLog);

    // Handle stats updates
    newSocket.on("stats_update", (stats) => {
      console.log("📊 Socket.IO: Received stats update:", stats);
      // You can add stats handling here if needed
    });

    // Add error event listeners
    newSocket.on("error", (error) => {
      console.error("❌ Socket.IO: Socket error:", error);
    });

    setSocket(newSocket);

    // Cleanup on unmount
    return () => {
      console.log("🧹 Socket.IO: Cleaning up connection");
      if (newSocket) {
        newSocket.off("new_log", handleNewLog);
        newSocket.off("new_info_log", handleNewLog);
        newSocket.off("new_error_log", handleNewLog);
        newSocket.off("new_request_log", handleNewLog);
        newSocket.close();
      }
    };
  }, [connectionAttempts]);

  // Utility functions
  const clearLogs = useCallback(() => setLogs([]), []);
  const clearErrors = useCallback(() => setErrors([]), []);
  const addLog = useCallback(
    (log) => setLogs((prev) => [log, ...prev.slice(0, 999)]),
    []
  );

  // Reconnect function
  const reconnect = useCallback(() => {
    if (socket) {
      console.log("🔄 Socket.IO: Manually reconnecting...");
      socket.connect();
    }
  }, [socket]);

  // Create socket API service
  const socketApi = useMemo(() => {
    if (socket && connected) {
      return createSocketLogService(socket);
    }
    return null;
  }, [socket, connected]);

  // Cleanup API service on unmount
  useEffect(() => {
    return () => {
      if (socketApi) {
        socketApi.cleanup();
      }
    };
  }, [socketApi]);

  const value = {
    socket,
    connected,
    logs,
    errors,
    addLog,
    clearLogs,
    clearErrors,
    reconnect,
    connectionAttempts,
    socketApi,
  };

  return (
    <SocketContext.Provider value={value}>{children}</SocketContext.Provider>
  );
};
