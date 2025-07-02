import axios from "axios";

const API_BASE_URL = "http://localhost:5000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(
      `Making ${config.method.toUpperCase()} request to ${config.url}`
    );
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error("API Error:", error);
    return Promise.reject(error);
  }
);

export const logService = {
  async getLogs(type = "all", level = null, week = null) {
    const params = new URLSearchParams();
    if (type) params.append("type", type);
    if (level) params.append("level", level);
    if (week) params.append("week", week);

    const response = await fetch(`${API_BASE_URL}/logs?${params}`);
    if (!response.ok) throw new Error("Failed to fetch logs");
    return response.json();
  },

  async getErrorLogs(week = null) {
    const params = new URLSearchParams();
    if (week) params.append("week", week);

    const response = await fetch(`${API_BASE_URL}/logs/errors?${params}`);
    if (!response.ok) throw new Error("Failed to fetch error logs");
    return response.json();
  },

  async getRequestLogs(week = null) {
    const params = new URLSearchParams();
    if (week) params.append("week", week);

    const response = await fetch(`${API_BASE_URL}/logs/requests?${params}`);
    if (!response.ok) throw new Error("Failed to fetch request logs");
    return response.json();
  },

  async getStats(week = null) {
    const params = new URLSearchParams();
    if (week) params.append("week", week);

    const response = await fetch(`${API_BASE_URL}/stats?${params}`);
    if (!response.ok) throw new Error("Failed to fetch stats");
    return response.json();
  },
};

export default api;
