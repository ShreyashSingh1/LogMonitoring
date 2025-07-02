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
  Tabs,
  Tab,
} from "@mui/material";
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
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
import { useSocket } from "../contexts/SocketContext";
import { logService } from "../services/api";
import { format, parseISO } from "date-fns";

const Dashboard = () => {
  const socket = useSocket();
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  const [logs, setLogs] = useState({
    info: [],
    error: [],
    request: [],
  });
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (!socket.socket) return; // Wait for socket to be initialized

    const handleInfoLog = (log) => {
      setLogs((prev) => ({
        ...prev,
        info: [log, ...prev.info].slice(0, 100),
      }));
      updateStats(log);
    };

    const handleErrorLog = (log) => {
      setLogs((prev) => ({
        ...prev,
        error: [log, ...prev.error].slice(0, 100),
      }));
      updateStats(log);
    };

    const handleRequestLog = (log) => {
      setLogs((prev) => ({
        ...prev,
        request: [log, ...prev.request].slice(0, 100),
      }));
      updateStats(log);
    };

    // Setup socket listeners
    socket.socket.on("new_info_log", handleInfoLog);
    socket.socket.on("new_error_log", handleErrorLog);
    socket.socket.on("new_request_log", handleRequestLog);

    // Cleanup listeners on unmount
    return () => {
      if (socket.socket) {
        socket.socket.off("new_info_log", handleInfoLog);
        socket.socket.off("new_error_log", handleErrorLog);
        socket.socket.off("new_request_log", handleRequestLog);
      }
    };
  }, [socket.socket]); // Only re-run when socket instance changes

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [allLogs, statsData] = await Promise.all([
        logService.getLogs(),
        logService.getStats(),
      ]);

      // Organize logs by type
      const organized = {
        info: allLogs.filter((log) => log.log_type === "info"),
        error: allLogs.filter((log) => log.log_type === "error"),
        request: allLogs.filter((log) => log.log_type === "request"),
      };
      setLogs(organized);
      setStats(statsData);
      updateChartData(allLogs);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  const updateStats = (newLog) => {
    setStats((prev) => {
      const updated = { ...prev };
      updated.total_logs++;
      updated.by_type[newLog.log_type] =
        (updated.by_type[newLog.log_type] || 0) + 1;
      updated.by_source[newLog.source] =
        (updated.by_source[newLog.source] || 0) + 1;
      updated.by_level[newLog.level] =
        (updated.by_level[newLog.level] || 0) + 1;
      return updated;
    });
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
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {!socket.connected && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Disconnected from log monitoring server. Real-time updates are not
          available.
        </Alert>
      )}

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
