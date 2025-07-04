import { useNavigate, useLocation } from "react-router-dom";
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Typography,
  Chip,
} from "@mui/material";
import {
  Dashboard as DashboardIcon,
  Article as LogsIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  Circle as StatusIcon,
} from "@mui/icons-material";
import { useSocket } from "../hooks/useSocket";

const drawerWidth = 240;

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { connected, logs, errors } = useSocket();

  const menuItems = [
    { path: "/", label: "Dashboard", icon: <DashboardIcon /> },
    { path: "/logs", label: "Log Viewer", icon: <LogsIcon /> },
    { path: "/analytics", label: "Analytics", icon: <AnalyticsIcon /> },
    { path: "/settings", label: "Settings", icon: <SettingsIcon /> },
  ];

  const handleNavigation = (path) => {
    navigate(path);
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        "& .MuiDrawer-paper": {
          width: drawerWidth,
          boxSizing: "border-box",
          backgroundColor: "#fafafa",
          borderRight: "1px solid #e0e0e0",
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <StatusIcon
            sx={{
              color: connected ? "success.main" : "error.main",
              mr: 1,
              fontSize: 16,
            }}
          />
          <Typography
            variant="body2"
            color={connected ? "success.main" : "error.main"}
          >
            {connected ? "Connected" : "Disconnected"}
          </Typography>
        </Box>

        <Box sx={{ display: "flex", gap: 1 }}>
          <Chip
            label={`${logs.length} Logs`}
            size="small"
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`${errors.length} Errors`}
            size="small"
            color="error"
            variant="outlined"
          />
        </Box>
      </Box>

      <Divider />

      <List>
        {menuItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              onClick={() => handleNavigation(item.path)}
              selected={location.pathname === item.path}
              sx={{
                "&.Mui-selected": {
                  backgroundColor: "primary.main",
                  color: "white",
                  "&:hover": {
                    backgroundColor: "primary.dark",
                  },
                  "& .MuiListItemIcon-root": {
                    color: "white",
                  },
                },
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
};

export default Navbar;
