import React, { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Pagination,
  IconButton,
  Collapse,
  Alert,
  Stack,
  LinearProgress,
} from "@mui/material";
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  DateRange as DateRangeIcon,
} from "@mui/icons-material";
import { format } from "date-fns";
import ReactJson from "react18-json-view";
import { useSocket, useSocketApi } from "../hooks/useSocket";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { LocalizationProvider, DateTimePicker } from "@mui/x-date-pickers";

const LogViewer = () => {
  const { logs: liveLogs, connected } = useSocket();
  const socketApi = useSocketApi();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [searchType, setSearchType] = useState("message");
  const [levelFilter, setLevelFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [selectedLog, setSelectedLog] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalLogs, setTotalLogs] = useState(0);
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [startTime, setStartTime] = useState(null);
  const [endTime, setEndTime] = useState(null);
  const [availableWeeks, setAvailableWeeks] = useState([]);
  const [selectedWeek, setSelectedWeek] = useState(null);
  const [error, setError] = useState(null);

  const itemsPerPage = 50;

  useEffect(() => {
    console.log("🔍 LogViewer: Search params changed:", {
      searchTerm,
      searchType,
      page,
      levelFilter,
      sourceFilter,
      startTime,
      endTime,
      selectedWeek,
    });
    fetchLogs();
  }, [
    page,
    levelFilter,
    sourceFilter,
    searchTerm,
    startTime,
    endTime,
    selectedWeek,
  ]);

  useEffect(() => {
    // Merge live logs with fetched logs
    console.log(
      `📡 LogViewer: Received ${liveLogs.length} live logs from Socket.IO`
    );
    if (liveLogs.length > 0) {
      setLogs((prevLogs) => {
        // Add new logs at the beginning
        const newLogs = [...liveLogs];

        // Create a Set of existing log identifiers
        const existingLogIds = new Set(
          prevLogs.map((log) => `${log.raw_content}-${log.timestamp}`)
        );

        // Only add logs that don't exist
        const uniqueNewLogs = newLogs.filter(
          (log) => !existingLogIds.has(`${log.raw_content}-${log.timestamp}`)
        );

        // Combine and sort by timestamp
        const combinedLogs = [...uniqueNewLogs, ...prevLogs]
          .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
          .slice(0, 1000); // Keep only last 1000 logs

        console.log(
          `✅ LogViewer: Added ${uniqueNewLogs.length} new logs (total: ${combinedLogs.length})`
        );
        return combinedLogs;
      });
    }
  }, [liveLogs]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);

      // Skip if socket API not available
      if (!socketApi) {
        console.log("🔄 LogViewer: Socket API not available, skipping fetch");
        setLoading(false);
        return;
      }

      const response = await socketApi.getLogs({
        type: "all",
        level: levelFilter !== "all" ? levelFilter : null,
        source: sourceFilter !== "all" ? sourceFilter : null,
        page,
        per_page: itemsPerPage,
        start_time: startTime ? startTime.toISOString() : null,
        end_time: endTime ? endTime.toISOString() : null,
        week: selectedWeek,
        search_term: searchTerm || null,
        search_type: searchType || null,
      });

      setLogs(response.logs);
      setTotalPages(response.total_pages);
      setTotalLogs(response.total);
      setSelectedWeek(response.week);
      setAvailableWeeks(response.available_weeks || []);
    } catch (error) {
      console.error("Error fetching logs:", error);
      setError("Failed to fetch logs. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogClick = (log) => {
    setSelectedLog(log);
    setDialogOpen(true);
  };

  const handleRowExpand = (index) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRows(newExpanded);
  };

  const handleRefresh = () => {
    setPage(1);
    fetchLogs();
  };

  const handleClearFilters = () => {
    setSearchTerm("");
    setLevelFilter("all");
    setSourceFilter("all");
    setStartTime(null);
    setEndTime(null);
    setSelectedWeek(null);
    setPage(1);
  };

  const getLogLevelIcon = (level) => {
    switch (level?.toLowerCase()) {
      case "error":
        return <ErrorIcon color="error" fontSize="small" />;
      case "warn":
      case "warning":
        return <WarningIcon color="warning" fontSize="small" />;
      case "info":
        return <InfoIcon color="info" fontSize="small" />;
      default:
        return <SuccessIcon color="success" fontSize="small" />;
    }
  };

  const getRowClass = (level) => {
    switch (level?.toLowerCase()) {
      case "error":
        return "log-entry-error";
      case "warn":
      case "warning":
        return "log-entry-warn";
      case "info":
        return "log-entry-info";
      default:
        return "";
    }
  };

  // Get unique sources and levels for filters
  const uniqueSources = [
    ...new Set(logs.map((log) => log.source).filter(Boolean)),
  ];
  const uniqueLevels = [
    ...new Set(logs.map((log) => log.level).filter(Boolean)),
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Log Viewer
        {connected && (
          <Chip label="Live" color="success" size="small" sx={{ ml: 2 }} />
        )}
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            {/* Search Section */}
            <Grid item xs={12} md={6}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={8}>
                  <TextField
                    fullWidth
                    size="small"
                    label={
                      searchType === "req_id"
                        ? "Enter Request ID (exact match)"
                        : "Search in Messages"
                    }
                    placeholder={
                      searchType === "req_id"
                        ? "e.g., req-123-abc"
                        : "Search log messages..."
                    }
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <SearchIcon sx={{ mr: 1, color: "action.active" }} />
                      ),
                      endAdornment: searchTerm && (
                        <IconButton
                          size="small"
                          onClick={() => setSearchTerm("")}
                        >
                          ×
                        </IconButton>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={4}>
                  <FormControl fullWidth size="small">
                    <Select
                      value={searchType}
                      onChange={(e) => setSearchType(e.target.value)}
                    >
                      <MenuItem value="message">Message</MenuItem>
                      <MenuItem value="req_id">Request ID</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </Grid>

            {/* Level Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Level</InputLabel>
                <Select
                  value={levelFilter}
                  onChange={(e) => setLevelFilter(e.target.value)}
                  label="Level"
                >
                  <MenuItem value="all">All Levels</MenuItem>
                  {uniqueLevels.map((level) => (
                    <MenuItem key={level} value={level}>
                      {level.charAt(0).toUpperCase() + level.slice(1)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Source Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Source</InputLabel>
                <Select
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  label="Source"
                >
                  <MenuItem value="all">All Sources</MenuItem>
                  {uniqueSources.map((source) => (
                    <MenuItem key={source} value={source}>
                      {source.charAt(0).toUpperCase() + source.slice(1)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Week Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Week</InputLabel>
                <Select
                  value={selectedWeek || ""}
                  onChange={(e) => setSelectedWeek(e.target.value || null)}
                  label="Week"
                >
                  <MenuItem value="">Current Week</MenuItem>
                  {availableWeeks.map((week) => (
                    <MenuItem key={week} value={week}>
                      Week {week.split("_W")[1]} ({week.split("_W")[0]})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Date Range */}
            <Grid item xs={12} md={3}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <Stack direction="row" spacing={1}>
                  <DateTimePicker
                    label="From"
                    value={startTime}
                    onChange={setStartTime}
                    slotProps={{ textField: { size: "small" } }}
                  />
                  <DateTimePicker
                    label="To"
                    value={endTime}
                    onChange={setEndTime}
                    slotProps={{ textField: { size: "small" } }}
                  />
                </Stack>
              </LocalizationProvider>
            </Grid>

            {/* Action Buttons */}
            <Grid item xs={12} md={2}>
              <Stack direction="row" spacing={1}>
                <Button
                  variant="outlined"
                  onClick={handleClearFilters}
                  startIcon={<FilterIcon />}
                >
                  Clear
                </Button>
                <Button
                  variant="contained"
                  onClick={handleRefresh}
                  startIcon={<RefreshIcon />}
                >
                  Refresh
                </Button>
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Loading Progress */}
      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Log Count */}
      <Typography variant="subtitle1" gutterBottom>
        Showing {logs.length} of {totalLogs} logs
      </Typography>

      {/* Logs Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox" />
              <TableCell>Timestamp</TableCell>
              <TableCell>Level</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Message</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logs.map((log, index) => (
              <React.Fragment key={`${log.timestamp}-${index}`}>
                <TableRow className={getRowClass(log.level)} hover>
                  <TableCell padding="checkbox">
                    <IconButton
                      size="small"
                      onClick={() => handleRowExpand(index)}
                    >
                      {expandedRows.has(index) ? (
                        <ExpandLessIcon />
                      ) : (
                        <ExpandMoreIcon />
                      )}
                    </IconButton>
                  </TableCell>
                  <TableCell>
                    {format(new Date(log.timestamp), "yyyy-MM-dd HH:mm:ss")}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      {getLogLevelIcon(log.level)}
                      <Typography variant="body2">
                        {log.level?.toUpperCase()}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{log.source}</TableCell>
                  <TableCell>{log.message}</TableCell>
                  <TableCell>
                    <Button size="small" onClick={() => handleLogClick(log)}>
                      Details
                    </Button>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell
                    colSpan={6}
                    style={{ paddingBottom: 0, paddingTop: 0 }}
                  >
                    <Collapse
                      in={expandedRows.has(index)}
                      timeout="auto"
                      unmountOnExit
                    >
                      <Box sx={{ margin: 1 }}>
                        <ReactJson
                          src={log}
                          theme="monokai"
                          displayDataTypes={false}
                          enableClipboard={false}
                          collapsed={2}
                        />
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      <Box sx={{ mt: 2, display: "flex", justifyContent: "center" }}>
        <Pagination
          count={totalPages}
          page={page}
          onChange={(e, value) => setPage(value)}
          color="primary"
        />
      </Box>

      {/* Log Details Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Log Details</DialogTitle>
        <DialogContent>
          {selectedLog && (
            <ReactJson
              src={selectedLog}
              theme="monokai"
              displayDataTypes={false}
              enableClipboard={false}
              collapsed={1}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LogViewer;
