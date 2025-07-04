import { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from "@mui/material";
import {
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from "@mui/icons-material";
import { useSocket, useSocketApi } from "../hooks/useSocket";

const Settings = () => {
  const { connected, clearLogs, clearErrors } = useSocket();
  const socketApi = useSocketApi();
  const [settings, setSettings] = useState({
    maxLogs: 1000,
    maxErrors: 100,
    autoRefresh: true,
    refreshInterval: 5000,
    showNotifications: true,
    highlightErrors: true,
  });
  const [stats, setStats] = useState({});
  const [csvFiles, setCsvFiles] = useState([]);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportSettings, setExportSettings] = useState({
    startDate: "",
    endDate: "",
    source: "all",
    level: "all",
  });
  const [saveMessage, setSaveMessage] = useState("");

  useEffect(() => {
    fetchStats();
    loadSettings();
  }, []);

  const loadSettings = () => {
    const savedSettings = localStorage.getItem("logMonitorSettings");
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  };

  const saveSettings = () => {
    localStorage.setItem("logMonitorSettings", JSON.stringify(settings));
    setSaveMessage("Settings saved successfully!");
    setTimeout(() => setSaveMessage(""), 3000);
  };

  const fetchStats = async () => {
    try {
      // Skip if socket API not available
      if (!socketApi) {
        console.log("🔄 Settings: Socket API not available, skipping fetch");
        return;
      }

      const data = await socketApi.getStats();
      setStats(data);
      setCsvFiles(data.csv_files || []);
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  };

  const handleSettingChange = (key, value) => {
    setSettings((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleExport = async () => {
    try {
      // This would typically call an export API endpoint
      console.log("Exporting with settings:", exportSettings);
      setExportDialogOpen(false);
      alert("Export functionality would be implemented here");
    } catch (error) {
      console.error("Error exporting:", error);
    }
  };

  const handleClearLogs = () => {
    if (
      window.confirm(
        "Are you sure you want to clear all live logs? This cannot be undone."
      )
    ) {
      clearLogs();
    }
  };

  const handleClearErrors = () => {
    if (
      window.confirm(
        "Are you sure you want to clear all live errors? This cannot be undone."
      )
    ) {
      clearErrors();
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      {saveMessage && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {saveMessage}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* System Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <List>
                <ListItem>
                  <ListItemText primary="Connection Status" />
                  <ListItemSecondaryAction>
                    <Chip
                      label={connected ? "Connected" : "Disconnected"}
                      color={connected ? "success" : "error"}
                      size="small"
                    />
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText primary="Total Logs in Database" />
                  <ListItemSecondaryAction>
                    <Typography variant="body2">
                      {stats.total_logs || 0}
                    </Typography>
                  </ListItemSecondaryAction>
                </ListItem>
                <ListItem>
                  <ListItemText primary="Recent Activity (1h)" />
                  <ListItemSecondaryAction>
                    <Typography variant="body2">
                      {stats.recent_activity || 0}
                    </Typography>
                  </ListItemSecondaryAction>
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Display Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Display Settings
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <TextField
                  label="Max Live Logs"
                  type="number"
                  value={settings.maxLogs}
                  onChange={(e) =>
                    handleSettingChange("maxLogs", parseInt(e.target.value))
                  }
                  helperText="Maximum number of logs to keep in memory"
                  fullWidth
                />
                <TextField
                  label="Max Live Errors"
                  type="number"
                  value={settings.maxErrors}
                  onChange={(e) =>
                    handleSettingChange("maxErrors", parseInt(e.target.value))
                  }
                  helperText="Maximum number of errors to keep in memory"
                  fullWidth
                />
                <TextField
                  label="Refresh Interval (ms)"
                  type="number"
                  value={settings.refreshInterval}
                  onChange={(e) =>
                    handleSettingChange(
                      "refreshInterval",
                      parseInt(e.target.value)
                    )
                  }
                  helperText="How often to refresh data in milliseconds"
                  fullWidth
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Notification Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Notification Settings
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.autoRefresh}
                      onChange={(e) =>
                        handleSettingChange("autoRefresh", e.target.checked)
                      }
                    />
                  }
                  label="Auto Refresh"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.showNotifications}
                      onChange={(e) =>
                        handleSettingChange(
                          "showNotifications",
                          e.target.checked
                        )
                      }
                    />
                  }
                  label="Show Browser Notifications"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.highlightErrors}
                      onChange={(e) =>
                        handleSettingChange("highlightErrors", e.target.checked)
                      }
                    />
                  }
                  label="Highlight Errors"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Data Management */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Data Management
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={fetchStats}
                  fullWidth
                >
                  Refresh Statistics
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<DownloadIcon />}
                  onClick={() => setExportDialogOpen(true)}
                  fullWidth
                >
                  Export Logs
                </Button>
                <Button
                  variant="outlined"
                  color="warning"
                  startIcon={<DeleteIcon />}
                  onClick={handleClearLogs}
                  fullWidth
                >
                  Clear Live Logs
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={handleClearErrors}
                  fullWidth
                >
                  Clear Live Errors
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* CSV Files */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Generated CSV Files
              </Typography>
              <List>
                {csvFiles.map((file, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={file.name}
                      secondary={`Size: ${formatFileSize(file.size)}`}
                    />
                    <ListItemSecondaryAction>
                      <Button
                        size="small"
                        startIcon={<DownloadIcon />}
                        onClick={() => {
                          // This would typically trigger a file download
                          console.log("Download file:", file.name);
                          alert(
                            "Download functionality would be implemented here"
                          );
                        }}
                      >
                        Download
                      </Button>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
                {csvFiles.length === 0 && (
                  <ListItem>
                    <ListItemText primary="No CSV files generated yet" />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Save Button */}
        <Grid item xs={12}>
          <Button
            variant="contained"
            color="primary"
            onClick={saveSettings}
            size="large"
          >
            Save Settings
          </Button>
        </Grid>
      </Grid>

      {/* Export Dialog */}
      <Dialog
        open={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Export Logs</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 1 }}>
            <TextField
              label="Start Date"
              type="date"
              value={exportSettings.startDate}
              onChange={(e) =>
                setExportSettings((prev) => ({
                  ...prev,
                  startDate: e.target.value,
                }))
              }
              InputLabelProps={{ shrink: true }}
              fullWidth
            />
            <TextField
              label="End Date"
              type="date"
              value={exportSettings.endDate}
              onChange={(e) =>
                setExportSettings((prev) => ({
                  ...prev,
                  endDate: e.target.value,
                }))
              }
              InputLabelProps={{ shrink: true }}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleExport} variant="contained">
            Export
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Settings;
