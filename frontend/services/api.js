// Socket-based API service for real-time communication
class SocketLogService {
  constructor(socket) {
    this.socket = socket;
    this.pendingRequests = new Map();
  }

  // Helper method to make socket requests with promises
  _makeSocketRequest(event, data = {}, responseEvent) {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.socket.connected) {
        reject(new Error("Socket not connected"));
        return;
      }

      const requestId = `${event}_${Date.now()}_${Math.random()}`;

      // Set up response listener
      const handleResponse = (response) => {
        this.socket.off(responseEvent, handleResponse);
        this.socket.off("error", handleError);
        this.pendingRequests.delete(requestId);
        resolve(response);
      };

      const handleError = (error) => {
        this.socket.off(responseEvent, handleResponse);
        this.socket.off("error", handleError);
        this.pendingRequests.delete(requestId);
        reject(new Error(error.message || "Socket request failed"));
      };

      // Store the request
      this.pendingRequests.set(requestId, {
        resolve,
        reject,
        event,
        responseEvent,
      });

      // Set up listeners
      this.socket.on(responseEvent, handleResponse);
      this.socket.on("error", handleError);

      // Send the request
      this.socket.emit(event, { ...data, requestId });

      // Set timeout
      setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.socket.off(responseEvent, handleResponse);
          this.socket.off("error", handleError);
          this.pendingRequests.delete(requestId);
          reject(new Error("Request timeout"));
        }
      }, 10000); // 10 second timeout
    });
  }

  async getLogs({
    type = "all",
    level = null,
    source = null,
    week = null,
    page = 1,
    per_page = 50,
    start_time = null,
    end_time = null,
    search_term = null,
    search_type = null,
  } = {}) {
    console.log("📡 Socket API: Getting logs with params:", {
      type,
      level,
      source,
      week,
      page,
      per_page,
      start_time,
      end_time,
      search_term,
      search_type,
    });

    return this._makeSocketRequest(
      "get_logs",
      {
        type,
        level,
        source,
        week,
        page,
        per_page,
        start_time,
        end_time,
        search_term,
        search_type,
      },
      "logs_response"
    );
  }

  async getErrorLogs({ week = null, page = 1, per_page = 50 } = {}) {
    console.log("📡 Socket API: Getting error logs");
    return this._makeSocketRequest(
      "get_error_logs",
      {
        week,
        page,
        per_page,
      },
      "error_logs_response"
    );
  }

  async getRequestLogs({
    week = null,
    source = null,
    status_code = null,
    page = 1,
    per_page = 50,
  } = {}) {
    console.log("📡 Socket API: Getting request logs");
    return this._makeSocketRequest(
      "get_request_logs",
      {
        week,
        source,
        status_code,
        page,
        per_page,
      },
      "request_logs_response"
    );
  }

  async getStats(week = null) {
    console.log("📡 Socket API: Getting stats");
    return this._makeSocketRequest("get_stats", { week }, "stats_response");
  }

  async getRequestStats(week = null) {
    console.log("📡 Socket API: Getting request stats");
    return this._makeSocketRequest(
      "get_request_stats",
      { week },
      "request_stats_response"
    );
  }

  async getSources(week = null) {
    console.log("📡 Socket API: Getting sources");
    return this._makeSocketRequest("get_sources", { week }, "sources_response");
  }

  async getLevels(week = null) {
    console.log("📡 Socket API: Getting levels");
    return this._makeSocketRequest("get_levels", { week }, "levels_response");
  }

  async searchLogs({
    q = "",
    type = null,
    source = null,
    level = null,
    start_time = null,
    end_time = null,
    field = "message",
    page = 1,
    per_page = 50,
  } = {}) {
    console.log("📡 Socket API: Searching logs");
    return this._makeSocketRequest(
      "search_logs",
      {
        q,
        type,
        source,
        level,
        start_time,
        end_time,
        field,
        page,
        per_page,
      },
      "search_logs_response"
    );
  }

  async getHealth() {
    console.log("📡 Socket API: Getting health status");
    return this._makeSocketRequest("get_health", {}, "health_response");
  }

  // Clean up any pending requests
  cleanup() {
    this.pendingRequests.clear();
  }
}

// Create a factory function to create the service with a socket
export const createSocketLogService = (socket) => {
  return new SocketLogService(socket);
};

// Main export - Socket-based API is the primary interface
export default createSocketLogService;
