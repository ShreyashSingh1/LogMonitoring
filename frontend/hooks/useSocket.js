import { useContext } from "react";
import { SocketContext } from "../contexts/SocketContextDef";

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error("useSocket must be used within a SocketProvider");
  }
  return context;
};

// Custom hook specifically for the socket API
export const useSocketApi = () => {
  const { socketApi, connected } = useSocket();

  if (!connected || !socketApi) {
    console.warn("Socket API not available - socket not connected");
    return null;
  }

  return socketApi;
};

export default useSocket;
