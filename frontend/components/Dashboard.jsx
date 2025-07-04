import { useState, useEffect } from "react";
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  AlertTitle,
  Tabs,
  Tab,
  Button,
} from "@mui/material";
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  Refresh as RefreshIcon,
} from "@mui/icons-material";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { useSocket, useSocketApi } from "../hooks/useSocket";
import { format, parseISO } from "date-fns";

const Dashboard = () => {
  const { socket, connected, reconnect, connectionAttempts } = useSocket();
  const socketApi = useSocketApi();
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  const [logs, setLogs] = useState({
    info: [],
    error: [],
    request: [],
  });
  const [chartData, setChartData] = useState([]);

  // Fetch initial data on component mount
  useEffect(() => {
    fetchInitialData();
  }, []);

  // Handle real-time log updates from socket
  useEffect(() => {
    if (!socket) {
      console.log("⏳ Dashboard: Waiting for socket connection...");
      return;
    }

    console.log("🔌 Dashboard: Setting up Socket.IO listeners");

    const handleConnectionEstablished = (data) => {
      console.log(
        "🤝 Dashboard: Processing connection established data:",
        data
      );

      // Set initial stats
      if (data.stats) {
        setStats(data.stats);
        console.log("📊 Dashboard: Set initial stats:", data.stats);
      }

      // Set initial logs if provided
      if (data.recent_logs && Array.isArray(data.recent_logs)) {
        console.log(
          `📝 Dashboard: Processing ${data.recent_logs.length} recent logs`
        );

        // Organize logs by type and keep only 10 most recent
        const organized = {
          info: data.recent_logs
            .filter((log) => log.log_type === "info")
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 10),
          error: data.recent_logs
            .filter((log) => log.log_type === "error")
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 10),
          request: data.recent_logs
            .filter((log) => log.log_type === "request")
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 10),
        };

        setLogs(organized);
        console.log("📝 Dashboard: Set initial logs:", organized);

        // Update chart data with recent logs
        updateChartData(data.recent_logs);
      }

      setLoading(false);
    };

    const handleNewLog = (log) => {
      console.log(`📝 Dashboard: Received ${log.log_type} log:`, log);

      // Update logs state based on log type
      setLogs((prev) => {
        const logType = log.log_type || "info";
        return {
          ...prev,
          [logType]: [log, ...(prev[logType] || [])].slice(0, 10),
        };
      });

      // Update chart data
      setChartData((prevData) => {
        const now = new Date();
        const logTime = parseISO(log.timestamp);
        const hoursDiff = Math.floor((now - logTime) / (1000 * 60 * 60));

        if (hoursDiff >= 0 && hoursDiff < 24) {
          return prevData.map((interval, index) => {
            if (index === 23 - hoursDiff) {
              const updatedInterval = { ...interval };
              if (log.log_type === "error") updatedInterval.errors++;
              else if (log.level === "warning") updatedInterval.warnings++;
              else if (log.log_type === "info") updatedInterval.info++;
              else if (log.log_type === "request") updatedInterval.requests++;
              return updatedInterval;
            }
            return interval;
          });
        }
        return prevData;
      });
    };

    // Setup socket listeners for all log types
    socket.on("connection_established", handleConnectionEstablished);
    socket.on("new_log", handleNewLog);
    socket.on("new_info_log", handleNewLog);
    socket.on("new_error_log", handleNewLog);
    socket.on("new_request_log", handleNewLog);

    // Add stats update listener
    socket.on("stats_update", (newStats) => {
      console.log("📊 Dashboard: Received stats update:", newStats);
      setStats(newStats);
    });

    // Cleanup listeners on unmount
    return () => {
      if (socket) {
        console.log("🧹 Dashboard: Cleaning up Socket.IO listeners");
        socket.off("connection_established", handleConnectionEstablished);
        socket.off("new_log", handleNewLog);
        socket.off("new_info_log", handleNewLog);
        socket.off("new_error_log", handleNewLog);
        socket.off("new_request_log", handleNewLog);
        socket.off("stats_update");
      }
    };
  }, [socket]); // Only re-run when socket instance changes

  // Show connection status
  useEffect(() => {
    console.log(
      `Socket connection status: ${connected ? "Connected" : "Disconnected"}`
    );
  }, [connected]);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      console.log("🔄 Dashboard: Starting initial data fetch...");

      // If connected, we'll get data from connection_established event
      // This is just a fallback if we need to manually fetch data
      if (!socketApi || !connected) {
        console.log(
          "🔄 Dashboard: Socket API not available or not connected, waiting for connection..."
        );
        // Don't set loading to false here, let connection_established handle it
        return;
      }

      // Fallback: manually fetch data if connection_established didn't provide it
      console.log("🔄 Dashboard: Manually fetching data as fallback...");
      const [logsResponse, statsData] = await Promise.all([
        socketApi.getLogs(),
        socketApi.getStats(),
      ]);

      // Access the logs array from the response
      const allLogs = logsResponse.logs || [];

      // Organize logs by type and keep only 10 most recent
      const organized = {
        info: allLogs
          .filter((log) => log.log_type === "info")
          .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
          .slice(0, 10),
        error: allLogs
          .filter((log) => log.log_type === "error")
          .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
          .slice(0, 10),
        request: allLogs
          .filter((log) => log.log_type === "request")
          .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
          .slice(0, 10),
      };
      setLogs(organized);
      setStats(statsData);
      updateChartData(allLogs);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching data:", error);
      setLoading(false);
    }
  };

  const updateChartData = (logs) => {
    const now = new Date();
    const intervals = [];

    // Create 24 hour intervals
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      intervals.push({
        time: format(time, "HH:mm"),
        errors: 0,
        warnings: 0,
        info: 0,
        requests: 0,
      });
    }

    // Count logs by hour and type
    logs.forEach((log) => {
      const logTime = parseISO(log.timestamp);
      const hoursDiff = Math.floor((now - logTime) / (1000 * 60 * 60));

      if (hoursDiff >= 0 && hoursDiff < 24) {
        const interval = intervals[23 - hoursDiff];
        if (interval) {
          if (log.log_type === "error") interval.errors++;
          else if (log.level === "warning") interval.warnings++;
          else if (log.log_type === "info") interval.info++;
          else if (log.log_type === "request") interval.requests++;
        }
      }
    });

    setChartData(intervals);
  };

  const getLogLevelIcon = (level) => {
    switch (level?.toLowerCase()) {
      case "error":
        return <ErrorIcon color="error" />;
      case "warn":
      case "warning":
        return <WarningIcon color="warning" />;
      case "info":
        return <InfoIcon color="info" />;
      default:
        return <SuccessIcon color="success" />;
    }
  };

  const getLogLevelColor = (level) => {
    switch (level?.toLowerCase()) {
      case "error":
        return "error";
      case "warn":
      case "warning":
        return "warning";
      case "info":
        return "info";
      default:
        return "success";
    }
  };

  const renderLogTable = (type) => {
    const logList = logs[type] || [];

    return (
      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Time</TableCell>
              <TableCell>Level</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Message</TableCell>
              {type === "request" && (
                <>
                  <TableCell>Method</TableCell>
                  <TableCell>Endpoint</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Response Time</TableCell>
                </>
              )}
              {type === "info" && (
                <>
                  <TableCell>Function</TableCell>
                  <TableCell>File</TableCell>
                </>
              )}
              <TableCell>User ID</TableCell>
              <TableCell>Request ID</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logList.map((log, index) => (
              <TableRow key={index}>
                <TableCell>
                  {format(parseISO(log.timestamp), "HH:mm:ss")}
                </TableCell>
                <TableCell>
                  <Chip
                    icon={getLogLevelIcon(log.level)}
                    label={log.level}
                    color={getLogLevelColor(log.level)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{log.source}</TableCell>
                <TableCell
                  sx={{
                    maxWidth: "300px",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {log.message}
                </TableCell>
                {type === "request" && (
                  <>
                    <TableCell>{log.method || "-"}</TableCell>
                    <TableCell>{log.endpoint || "-"}</TableCell>
                    <TableCell>
                      <Chip
                        label={log.status_code}
                        color={log.status_code < 400 ? "success" : "error"}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {log.response_time ? `${log.response_time}ms` : "-"}
                    </TableCell>
                  </>
                )}
                {type === "info" && (
                  <>
                    <TableCell>{log.function || "-"}</TableCell>
                    <TableCell>{log.filename || "-"}</TableCell>
                  </>
                )}
                <TableCell>{log.user_id || "-"}</TableCell>
                <TableCell>{log.req_id || "-"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  if (loading) {
    return (
      <Box sx={{ width: "100%", mt: 2 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading dashboard...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Connection Status Alert */}
      {!connected && (
        <Alert
          severity="warning"
          sx={{ mb: 2 }}
          action={
            <Button
              color="inherit"
              size="small"
              onClick={reconnect}
              startIcon={<RefreshIcon />}
            >
              Reconnect
            </Button>
          }
        >
          <AlertTitle>Connection Lost</AlertTitle>
          Disconnected from log monitoring server. Real-time updates are not
          available.
          {connectionAttempts > 0 && (
            <Box component="span" sx={{ ml: 1 }}>
              (Attempt {connectionAttempts})
            </Box>
          )}
        </Alert>
      )}

      {/* Connected Status */}
      {connected && (
        <Alert severity="success" sx={{ mb: 2 }}>
          <AlertTitle>Connected</AlertTitle>
          Receiving real-time log updates
        </Alert>
      )}

      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Stats Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Logs
              </Typography>
              <Typography variant="h4">{stats.total_logs || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Error Rate
              </Typography>
              <Typography variant="h4" color="error">
                {stats.by_level?.error || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Node Logs
              </Typography>
              <Typography variant="h4" color="primary">
                {stats.by_source?.node || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Python Logs
              </Typography>
              <Typography variant="h4" color="secondary">
                {stats.by_source?.python || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Charts */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Log Activity (24h)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="errors"
                    stroke="#f44336"
                    name="Errors"
                  />
                  <Line
                    type="monotone"
                    dataKey="warnings"
                    stroke="#ff9800"
                    name="Warnings"
                  />
                  <Line
                    type="monotone"
                    dataKey="info"
                    stroke="#2196f3"
                    name="Info"
                  />
                  <Line
                    type="monotone"
                    dataKey="requests"
                    stroke="#4caf50"
                    name="Requests"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Log Tables */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Tabs
                value={activeTab}
                onChange={(e, newValue) => setActiveTab(newValue)}
              >
                <Tab label="Info Logs" />
                <Tab label="Error Logs" />
                <Tab label="Request Logs" />
              </Tabs>

              {activeTab === 0 && renderLogTable("info")}
              {activeTab === 1 && renderLogTable("error")}
              {activeTab === 2 && renderLogTable("request")}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
