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
    const params = new URLSearchParams();
    if (type) params.append("type", type);
    if (level) params.append("level", level);
    if (source) params.append("source", source);
    if (week) params.append("week", week);
    if (page) params.append("page", page);
    if (per_page) params.append("per_page", per_page);
    if (start_time) params.append("start_time", start_time);
    if (end_time) params.append("end_time", end_time);
    if (search_term) params.append("search_term", search_term);
    if (search_type) params.append("search_type", search_type);

    const response = await fetch(`${API_BASE_URL}/logs?${params}`);
    if (!response.ok) throw new Error("Failed to fetch logs");
    return response.json();
  },

  async getErrorLogs({ week = null, page = 1, per_page = 50 } = {}) {
    const params = new URLSearchParams();
    if (week) params.append("week", week);
    if (page) params.append("page", page);
    if (per_page) params.append("per_page", per_page);

    const response = await fetch(`${API_BASE_URL}/logs/errors?${params}`);
    if (!response.ok) throw new Error("Failed to fetch error logs");
    return response.json();
  },

  async getRequestLogs({
    week = null,
    source = null,
    status_code = null,
    page = 1,
    per_page = 50,
  } = {}) {
    const params = new URLSearchParams();
    if (week) params.append("week", week);
    if (source) params.append("source", source);
    if (status_code) params.append("status_code", status_code);
    if (page) params.append("page", page);
    if (per_page) params.append("per_page", per_page);

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

  async getRequestStats(week = null) {
    const params = new URLSearchParams();
    if (week) params.append("week", week);

    const response = await fetch(`${API_BASE_URL}/stats/requests?${params}`);
    if (!response.ok) throw new Error("Failed to fetch request stats");
    return response.json();
  },
};

export default api;
